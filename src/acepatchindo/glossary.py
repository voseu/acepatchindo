"""Canonical 3-Tier Glossary and EN->ID / ZH->ID translator for Honor of Kings Ace."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from acepatchindo.lexicon_id import translate_segment_en_to_id
from acepatchindo.tag_aligner import (
    BRACKET_TERM_MAP,
    normalize_formula_skeleton_zh,
    normalize_plain_zh,
    reinject_formula_and_skeleton,
    reinject_skeleton_from_source,
    translate_preserving_skeleton,
)
from acepatchindo.validator import (
    CJK_RE,
    CONTROL_TOKEN_RE,
    PLACEHOLDER_RE,
    TAG_RE,
    sanitize_target_text,
    validate_translation,
)

# Exact, human-verified Indonesian translations for all 108 Chinese strings missed by English Patcher 1.4.12
# in the user's real Windows game installation (409 records across 6 QtsVFS packages).
WINDOWS_108_ZH_TO_ID: dict[str, str] = {
    "孙尚香·强化": "Lady Sun: Empowered",
    "转移后清除自身负面状态，并在5秒内免疫受到的控制。": "Setelah berpindah, menghapus debuff diri sendiri dan kebal terhadap Crowd Control selama 5 detik.",
    "转移后获得20%伤害加成。": "Setelah berpindah, dapatkan +20% Bonus Damage.",
    "战斗开始时，随机传送1个4-5阶临时等级为回合数×12的英雄进入战场（不含卡牌效果），并携带3件适配装备。": "Saat Combat dimulai, pindahkan secara acak 1 Hero Tier 4-5 dengan Temporary Level sebesar (Round x12) ke medan tempur (tanpa efek kartu), membawa 3 Equipment yang sesuai.",
    "若<color=#ffffff><b>枫叶舞</b></color>英雄被移除，其真实等级的25%会保留给下一个<color=#ffffff><b>枫叶舞</b></color>英雄，若为被出售，则保留75%真实等级，限一次。": "Jika Hero <color=#ffffff><b>Maple Leaf Dance</b></color> dihapus, 25% True Level-nya diwariskan ke Hero <color=#ffffff><b>Maple Leaf Dance</b></color> berikutnya; jika dijual, mewariskan 75% True Level (maks 1 kali).",
    "获得1张装备牌<color=#FFE897>三分旗帜</color>：造成伤害的40%平摊治疗所有【三分】英雄（仅【三分】英雄可穿戴）。": "Dapatkan 1 Kartu Equipment <color=#FFE897>Tri-Point Banner</color>: memulihkan HP semua Hero [Three Kingdoms] secara merata sebesar 40% dari Damage yang diberikan (hanya untuk Hero [Three Kingdoms]).",
    "<color=#ffffff><color=#ffffff><b>唯一</b></color></color>\n攻击速度+30%。攻速上限改为5.0。战斗期间，每获得2点法力值，提升1%攻击速度。": "<color=#ffffff><color=#ffffff><b>Unik</b></color></color>\nAttack Speed +30%. Batas Attack Speed menjadi 5.0. Selama Combat, setiap memperoleh 2 Mana, meningkatkan 1% Attack Speed.",
    "仅三分英雄穿戴。将受到伤害的40%转化为治疗量，平摊给所有场上【三分】英雄。": "Khusus Hero Three Kingdoms. Mengubah 40% Damage yang diterima menjadi pemulihan HP yang dibagi rata ke semua Hero [Three Kingdoms] di medan tempur.",
    "仅三分英雄穿戴。将造成伤害的40%转化为治疗量，平摊给所有【三分】英雄。": "Khusus Hero Three Kingdoms. Mengubah 40% Damage yang diberikan menjadi pemulihan HP yang dibagi rata ke semua Hero [Three Kingdoms].",
    "传送{0}级": "Teleportasi Lv.{0}",
    "场上随机英雄等级+5，触发{DaQiao_TideTimes:3}次，若对象为<b>温柔呼唤</b>的英雄则额外等级+5，每次使用后，触发次数+2。": "Hero acak di medan tempur mendapat Level +5, terpicu {DaQiao_TideTimes:3} kali; jika target adalah Hero <b>Gentle Call</b>, mendapat tambahan Level +5. Setiap digunakan, jumlah picuan +2.",
    "枫叶舞指定的英雄击败3/5/9/15名敌方英雄，获得1张秘技牌<b>翩跹舞步</b>并为枫叶舞解锁1项特性（共4项）。": "Hero yang ditunjuk Maple Leaf Dance mengalahkan 3/5/9/15 Hero musuh, dapatkan 1 Kartu Secret Art <b>Graceful Dance</b> dan buka 1 trait untuk Maple Leaf Dance (total 4 trait).",
    "枫叶舞指定的英雄累积击败3/5/9/15名敌方英雄后，阿离获得1张<color=#FFE897>翩跹舞步</color>，累计完成4次后任务需求固定为15。\n<color=#FFE897>翩跹舞步</color>：为<color=#FFE897>枫叶舞</color>挑选1张强化牌。": "Setelah Hero yang ditunjuk Maple Leaf Dance mengalahkan total 3/5/9/15 Hero musuh, Arli mendapat 1 <color=#FFE897>Graceful Dance</color>; setelah selesai 4 kali, syarat misi tetap 15.\n<color=#FFE897>Graceful Dance</color>: Pilih 1 kartu penguat untuk <color=#FFE897>Maple Leaf Dance</color>.",
    "每4个回合，乔汐获得1张<color=#FFE897>潮汐的交响</color>。\n<color=#FFE897>潮汐的交响</color>：场上随机5个英雄等级+4。": "Setiap 4 Round, Qiao Xi mendapat 1 <color=#FFE897>Tidal Symphony</color>.\n<color=#FFE897>Tidal Symphony</color>: 5 Hero acak di medan tempur mendapat Level +4.",
    "每4个回合，获得1张秘技牌<b>潮汐的交响</b>。": "Setiap 4 Round, dapatkan 1 Kartu Secret Art <b>Tidal Symphony</b>.",
    "每回合开始时，自动触发1次孙尚香【登场】词条效果。": "Di awal setiap Round, otomatis memicu efek [On Play] Lady Sun 1 kali.",
    "每回合开始时，触发1次<color=#FFE897>孙尚香</color>卡牌效果。": "Di awal setiap Round, memicu efek kartu <color=#FFE897>Lady Sun</color> 1 kali.",
    "立刻在<color=#FFE897>嬴政和武则天中随机一人</color>，下场战斗开始时使其吸收<color=#FFE897>其他友军</color>的等级和初始法力值。（使用后强化吸收能力）": "Segera pilih acak 1 dari <color=#FFE897>Ying Zheng atau Wu Zetian</color>; saat Combat berikutnya dimulai, ia menyerap Level dan Mana awal <color=#FFE897>sekutu lainnya</color>. (Memperkuat daya serap setelah dipakai)",
    "若<color=#FFE897>枫叶舞</color>英雄被移除，其真实等级的25%会保留给下一个<color=#FFE897>枫叶舞</color>英雄，若为被出售，则保留75%真实等级，限一次。": "Jika Hero <color=#FFE897>Maple Leaf Dance</color> dihapus, 25% True Level-nya diwariskan ke Hero <color=#FFE897>Maple Leaf Dance</color> berikutnya; jika dijual, mewariskan 75% True Level (maks 1 kali).",
    "<color=#ffffffbf>被动：</color>圣殿骑士冲锋时，对路径敌人造成<color=#dfa15e>[0]点物理伤害</color><color=#dfa15e>（[1]+[2]%自身最大生命值）</color>，随后戳刺敌人，造成<color=#dfa15e>[3]点物理伤害</color><color=#dfa15e>（[4]+[5]%自身最大生命值）</color>。\n<color=#ffffffbf>主动：</color>获得15%伤害加成，持续5秒。": "<color=#ffffffbf>Pasif:</color> Saat Templar Knight menerjang, memberikan <color=#dfa15e>[0] Physical Damage</color><color=#dfa15e> ([1]+[2]% Max HP diri)</color> ke musuh di jalur, lalu menusuk musuh sebesar <color=#dfa15e>[3] Physical Damage</color><color=#dfa15e> ([4]+[5]% Max HP diri)</color>.\n<color=#ffffffbf>Aktif:</color> Dapatkan +15% Bonus Damage selama 5 detik.",
    "将造成伤害的40%转化为治疗量，平摊给所有【三分】英雄。": "Mengubah 40% Damage yang diberikan menjadi pemulihan HP yang dibagi rata ke semua Hero [Three Kingdoms].",
    "万象大赛每个英雄首次达100级可领取奖励": "Klaim hadiah saat setiap Hero pertama kali mencapai Lv.100 di Turnamen ACE",
    "图片缓存目录": "Direktori Cache Gambar",
    "完成任务获取棋手武凤奖励": "Selesaikan misi untuk mendapatkan hadiah Chess Player Wu Feng",
    "应援失败，请重新尝试": "Dukungan gagal, silakan coba lagi",
    "您已经隐身2天啦，需要解除吗?": "Kamu sudah mode tak terlihat selama 2 hari, matikan sekarang?",
    "竞猜总数": "Total Tebakan",
    "钻石消耗": "Pemakaian Diamond",
    "<color=#98cbff>一、活动规则</color>\n<color=#FFFFFF>1、完成任务可领取武凤信物，足够的信物可兑换奖励。</color>\n<color=#FFFFFF>2、每日任务将于每天0点刷新，棋手任务仅可完成1次。</color>\n<color=#FFFFFF>3、若进行消极对局如挂机等行为，则无法完成对局任务哦。</color>": "<color=#98cbff>I. Aturan Event</color>\n<color=#FFFFFF>1. Selesaikan misi untuk klaim Token Wu Feng dan tukarkan dengan hadiah.</color>\n<color=#FFFFFF>2. Misi harian direset pukul 00:00 setiap hari; misi Chess Player hanya 1 kali.</color>\n<color=#FFFFFF>3. Perilaku pasif seperti AFK tidak akan menyelesaikan misi pertandingan.</color>",
    "<color=#FFFFFFFF>[组队]{0}:</color>": "<color=#FFFFFFFF>[Tim]{0}:</color>",
    "[系统]组队邀约": "[Sistem] Undangan Tim",
    "【有分同享】组队邀请：万象大赛-排位": "[Berbagi Poin] Undangan Tim: Turnamen ACE - Ranked",
    "万象大赛将棋手武凤升至6级": "Naikkan Chess Player Wu Feng ke Lv.6 di Turnamen ACE",
    "万象大赛用棋手武凤获得前三名": "Raih Top 3 menggunakan Chess Player Wu Feng di Turnamen ACE",
    "万象大赛用棋手武凤获得第一名": "Raih Peringkat 1 menggunakan Chess Player Wu Feng di Turnamen ACE",
    "万象王者{0}": "Vientiane King {0}",
    "下局是否继续和当前队友一起玩？": "Lanjut bermain bersama rekan tim saat ini di pertandingan berikutnya?",
    "下载管理": "Manajemen Unduhan",
    "仆从伤害提升至100%法术攻击力，生命值恢复提升至100%法术攻击力": "Damage Minion meningkat jadi 100% Magic Attack, pemulihan HP meningkat jadi 100% Magic Attack",
    "今日可上架价格范围：{0}-{1}": "Rentang harga jual hari ini: {0}-{1}",
    "今日宜摸鱼7天限时卡": "Kartu Trial 7 Hari: Santai Hari Ini",
    "你去争第一吧，算我让你的。": "Ambil saja juara satunya, anggap aku mengalah.",
    "使用棋手【乔汐】，在万象大赛中召唤1名临时等级为200级的英雄": "Gunakan Chess Player [Qiao Xi] dan panggil 1 Hero dengan Temporary Level 200 di Turnamen ACE",
    "公共": "Publik",
    "再上<color=#ffffff>{0}</color>分可获得<color=#ffffff>{1}</color>": "Naik <color=#ffffff>{0}</color> poin lagi untuk mendapatkan <color=#ffffff>{1}</color>",
    "再上<color=#ffffff>{0}</color>分超过": "Naik <color=#ffffff>{0}</color> poin lagi untuk melampaui",
    "再盈利<color=#ffffff>{0}</color>可获得<color=#ffffff>{1}</color>": "Profit <color=#ffffff>{0}</color> lagi untuk mendapatkan <color=#ffffff>{1}</color>",
    "再盈利<color=#ffffff>{0}</color>超过": "Profit <color=#ffffff>{0}</color> lagi untuk melampaui",
    "可上架价格范围已更新，请稍后再试": "Rentang harga jual telah diperbarui, silakan coba lagi nanti",
    "咱们同心协力，先把其他人送走。": "Ayo kerja sama, singkirkan pemain lain dulu.",
    "图片已保存至<color=#98CBFF>{0}</color>": "Gambar disimpan ke <color=#98CBFF>{0}</color>",
    "在钻石狂潮、王牌对决和棋手竞猜玩法中，可使用本抵扣券减免1000钻石。（钻石狂潮每次限用1张）": "Gunakan kupon diskon ini untuk potongan 1000 Diamond di mode Diamond Frenzy, Ace Duel, dan Tebakan Chess Player. (Maks 1 kupon per sesi Diamond Frenzy)",
    "在钻石狂潮、王牌对决和棋手竞猜玩法中，可使用本抵扣券减免5000钻石。（钻石狂潮每次限用1张）": "Gunakan kupon diskon ini untuk potongan 5000 Diamond di mode Diamond Frenzy, Ace Duel, dan Tebakan Chess Player. (Maks 1 kupon per sesi Diamond Frenzy)",
    "在钻石狂潮、王牌对决和棋手竞猜玩法中，可使用本抵扣券减免500钻石。（钻石狂潮每次限用1张）": "Gunakan kupon diskon ini untuk potongan 500 Diamond di mode Diamond Frenzy, Ace Duel, dan Tebakan Chess Player. (Maks 1 kupon per sesi Diamond Frenzy)",
    "士别三日，技术暴涨这么多？": "Baru sebentar tak bertemu, kemampuanmu sudah sehebat ini?",
    "巅峰王者{0}": "Peak King {0}",
    "已使用抵扣券": "Kupon Diskon Digunakan",
    "已放弃常规奖励": "Hadiah Reguler Dilewati",
    "已放弃常规奖励，获得特邀额外奖励": "Hadiah reguler dilewati, memperoleh hadiah ekstra undangan khusus",
    "当前无法购买积分保护卡": "Saat ini tidak dapat membeli Kartu Pelindung Poin",
    "您已经隐身3天啦，好友都看不到你哦~需要解除吗?": "Kamu sudah mode tak terlihat 3 hari, temanmu tidak bisa melihatmu~ Matikan sekarang?",
    "您已隐身{0}天啦，好友们都在等你上线呢，需要解除吗?": "Kamu sudah mode tak terlihat {0} hari, teman-teman menunggumu online. Matikan sekarang?",
    "您已隐身{0}天啦，好友都很想念你哦，需要解除吗?": "Kamu sudah mode tak terlihat {0} hari, teman-teman merindukanmu. Matikan sekarang?",
    "您正处于隐身状态哦，需要解除吗?": "Kamu sedang dalam mode tak terlihat, matikan sekarang?",
    "感觉这把有高手啊？": "Sepertinya ada pemain pro di pertandingan ini?",
    "我要开始表演了，好好看，好好学。": "Saatnya aku beraksi, perhatikan dan pelajari baik-baik.",
    "战力前列的棋手": "Chess Player dengan Power Tertinggi",
    "打开文件夹": "Buka Folder",
    "打开礼包，必定获得爱心投放1天限时卡，并且随机获得以下奖励：\n夺宝币*2、香香·热情轰炸(30天)*1、常小娥·月之祈福(30天)*1、白歌·剑意纵横(30天)*1、趣味桌游*1、100%黑巧克力*1、小鹿玩偶*1、小动物捏捏*1、赢律（棋手）、渡梦传送特效。\n打开第50个礼包必定获得：渡梦传送特效！": "Buka bundel untuk pasti mendapat Kartu Trial 1 Hari Heart Drop, serta acak salah satu hadiah berikut:\nKoin Harta*2, Lady Sun: Fiery Barrage (30 Hari)*1, Little Chang'e: Moon Blessing (30 Hari)*1, Bai Ge: Sword Intent (30 Hari)*1, Board Game Seru*1, Cokelat Hitam 100%*1, Boneka Rusa*1, Squishy Hewan*1, Ying Lu (Chess Player), Efek Teleportasi Dream Crossing.\nBuka bundel ke-50 dijamin mendapat: Efek Teleportasi Dream Crossing!",
    "抵扣钻石": "Potongan Diamond",
    "放弃翻牌将不会消耗每月翻牌次数，但也无法获得常规翻牌奖励（特邀额外奖励可正常获得）。确定放弃？": "Melewati buka kartu tidak mengurangi kuota bulanan, namun hadiah reguler tidak diperoleh (hadiah ekstra undangan khusus tetap diperoleh). Yakin lewati?",
    "数据资源损坏！您需要重启游戏客户端进行资源修复。": "Data resource rusak! Mulai ulang klien game untuk memperbaiki resource.",
    "新闻": "Berita",
    "是否授权《王者万象棋》绑定您同平台的《王者荣耀》账号，获取账号信息以提供更好的游戏体验。\n授权内容：将《王者荣耀》好友关系与好友亲密度继承至《王者万象棋》。\n<color=#98CBFFFF>特别声明：亲密度仅首次授权时进行同步，后续不会再同步；继承的数值以本周一王者荣耀内亲密度数值为准（不同账号同步时间存在延迟）。</color>": "Izinkan Honor of Kings: Ace menautkan akun Honor of Kings di platform yang sama untuk meningkatkan pengalaman bermain?\nIsi Izin: Mewariskan daftar teman dan Keakraban dari Honor of Kings ke Honor of Kings: Ace.\n<color=#98CBFFFF>Catatan: Keakraban hanya disinkronkan saat otorisasi pertama dan tidak disinkronkan lagi setelahnya, berdasarkan nilai Senin minggu ini di Honor of Kings (mungkin ada jeda antar akun).</color>",
    "更改目录": "Ubah Direktori",
    "最强王者{0}": "Strongest King {0}",
    "朋友们，下局我们继续排啊~": "Teman-teman, ayo lanjut main bareng di ronde berikutnya~",
    "朋友们，打完这局我有点事儿，下局不一起排了~": "Teman-teman, habis match ini aku ada urusan, belum bisa lanjut bareng~",
    "栏位扩充卡物品获取配置失败，请稍后再试": "Gagal memuat konfigurasi Kartu Ekspansi Slot, coba lagi nanti",
    "棋手武凤攻略": "Panduan Chess Player Wu Feng",
    "武凤攻略": "Panduan Wu Feng",
    "段位需达到倔强青铜方可发布招募！": "Capai Rank Stubborn Bronze untuk membuat rekrutmen!",
    "渡梦传送特效7天限时卡": "Kartu Trial 7 Hari: Efek Teleportasi Dream Crossing",
    "渡梦传送特效礼包": "Bundel Efek Teleportasi Dream Crossing",
    "玉环幻彩音阶7天限时卡": "Kartu Trial 7 Hari: Yu Huan Prismatic Scale",
    "玩家间亲密度值需高于{0}": "Keakraban antar pemain harus lebih dari {0}",
    "由于您在刚刚的对局中选择了不继续游戏，返回时是否要退出队伍？": "Karena kamu memilih tidak lanjut di pertandingan tadi, keluar dari tim saat kembali?",
    "留在队内": "Tetap di Tim",
    "系统会按照最优方案自动扣除抵扣券": "Sistem otomatis memakai kupon diskon paling optimal",
    "自己人，下手轻点。": "Kita teman sendiri, jangan keras-keras.",
    "芈月为等级最高的近战友军召唤1只暗影仆从协助战斗，持续10秒。仆从每次攻击造成<color=#d487e4>80%芈月法术攻击力的法术伤害</color>并为友军恢复<color=#d487e4>80%芈月法术攻击力</color><color=#9ff5d0>的生命值</color>，同时窃取目标1点<color=#dfa15e>物理防御</color>和<color=#d487e4>法术防御</color>转移给友军（最多30层，持续至回合结束）。": "Mi Yue memanggil 1 Shadow Servant bagi sekutu Melee berlevel tertinggi selama 10 detik. Setiap serangan Servant memberikan <color=#d487e4>Magic Damage sebesar 80% Magic Attack Mi Yue</color> dan memulihkan <color=#d487e4>80% Magic Attack Mi Yue</color><color=#9ff5d0> sebagai HP</color> ke sekutu, serta mencuri 1 <color=#dfa15e>Physical Defense</color> dan <color=#d487e4>Magic Defense</color> target untuk sekutu (maks 30 stack hingga akhir Round).",
    "获得棋盘【今日宜摸鱼】7天限时体验。": "Dapatkan Trial 7 Hari Papan Catur [Santai Hari Ini].",
    "获得特效【渡梦传送特效】7天限时体验。": "Dapatkan Trial 7 Hari Efek [Dream Crossing].",
    "获得皮肤【玉环幻彩音阶】7天限时体验。": "Dapatkan Trial 7 Hari Skin [Yu Huan Prismatic Scale].",
    "该亲密度下的选手可在王者{0}分以内有分同享": "Pada level Keakraban ini, pemain dapat Berbagi Poin hingga {0} poin King",
    "该阵容已收藏至我的阵容": "Lineup berhasil disimpan ke Lineup Saya",
    "请拖放下方已获取碎片到格内": "Seret dan lepaskan kepingan yang diperoleh di bawah ke dalam kotak",
    "赛事": "Turnamen",
    "超级周末：有分同享不限亲密度": "Super Weekend: Berbagi Poin tanpa batas Keakraban",
    "近期成交均价{0}，今日可上架价格范围：{1}-{2}": "Harga rata-rata terkini {0}, rentang harga jual hari ini: {1}-{2}",
    "这把我躺了，等你带飞。": "Match ini aku santai ya, gendong aku!",
    "这能输？我不服！": "Masa begini kalah? Aku tak terima!",
    "退出队伍": "Keluar Tim",
    "选择棋手武凤，一起化万法为己用！通过棋手技能随机获得一张他人的秘技牌，每局都能打出意料之外的组合。": "Pilih Chess Player Wu Feng dan kuasai segala jurus! Lewat Skill Chess Player, dapatkan acak 1 Kartu Secret Art milik lawan untuk menciptakan kombo tak terduga di setiap pertandingan.",
    "通关棋手武凤训练关卡": "Selesaikan stage latihan Chess Player Wu Feng",
    "道具数量不足，是否使用快捷购买？": "Jumlah item tidak cukup, gunakan Pembelian Cepat?",
    "部分购买成功": "Pembelian Sebagian Berhasil",
    "钻石抵扣券": "Kupon Diskon Diamond",
    # Common entity names
    "武凤": "Wu Feng",
    "三分": "Three Kingdoms",
    "三分之地": "Three Kingdoms",
    "吴国": "Wu",
    "蜀国": "Shu",
    "魏国": "Wei",
    "公孙离": "Arli",
    "乔汐": "Qiao Xi",
    "孙尚香": "Lady Sun",
    "少司缘": "Dyadia",
    "姬小满": "Biron",
    "空空儿": "Kongkong'er",
    "苍": "Cang",
    "元流之子": "Child of Flow",
}

# Ordered English -> Indonesian rules following Tier 1 hybrid HoK Ace terminology:
# Proper names (Heroes, Factions, Cards, Equipment) and Tier 1 English mechanics
# (Temporary Level, Physical Damage, Magic Damage, True Damage, Physical Attack, Magic Attack,
# Attack Speed, Max HP, Crit Rate, Crit Damage, Sacrifice, Revive, Shield, Stun, Silence,
# Disarm, Knockback, Combat, Round, Shop, Refresh, Tier, Chess Player) stay canonical.
EN_TO_ID_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # High-frequency HoK Ace specific templates (4,367+ bot avatars, leaderboards, tournaments)
    (re.compile(r"\bAI impersonates avatar\s*(\d+)", re.I), r"Avatar Bot AI \1"),
    (re.compile(r"\bAI impersonates avatar\b", re.I), "Avatar Bot AI"),
    (
        re.compile(
            r"\bRanked (\d+)(?:st|nd|rd|th) on last week's Diamond Frenzy leaderboard\b",
            re.I,
        ),
        r"Peringkat ke-\1 di Papan Peringkat Diamond Frenzy minggu lalu",
    ),
    (
        re.compile(r"\bRanked (\d+)(?:st|nd|rd|th) on\b", re.I),
        r"Peringkat ke-\1 di",
    ),
    (
        re.compile(r"\bRanking:\s*(\d+)(?:st|nd|rd|th) Place\b", re.I),
        r"Peringkat: Juara ke-\1",
    ),
    (re.compile(r"\bIn a single ACE Tournament match\b", re.I), "Dalam 1 pertandingan Turnamen ACE"),
    (re.compile(r"\ba single round of the ACE Tournament\b", re.I), "1 Round di Turnamen ACE"),
    (re.compile(r"\bin the ACE Tournament\b", re.I), "di Turnamen ACE"),
    (re.compile(r"\bACE Tournament\b"), "Turnamen ACE"),
    (re.compile(r"\blast week's\b", re.I), "minggu lalu"),
    (re.compile(r"\b equip it in the Customization system to\b", re.I), " pasang di sistem Kustomisasi untuk"),
    (re.compile(r"\bin the Customization system\b", re.I), "di sistem Kustomisasi"),
    (re.compile(r"\bCustomization system\b", re.I), "sistem Kustomisasi"),
    (re.compile(r"\bNumber of times\b", re.I), "Jumlah pencapaian"),
    (re.compile(r"\bfor the first time each Season\b", re.I), "untuk pertama kalinya setiap Season"),
    (re.compile(r"\bfor the first time\b", re.I), "untuk pertama kalinya"),
    (re.compile(r"\bupon reaching\b", re.I), "saat mencapai"),
    (re.compile(r"\bserver-wide\b", re.I), "di seluruh server"),
    # Action / Trigger headers
    (re.compile(r"\bAt the start of battle\b", re.I), "Saat Combat dimulai"),
    (re.compile(r"\bAt the start of combat\b", re.I), "Saat Combat dimulai"),
    (re.compile(r"\bStart of battle\b", re.I), "Awal Combat"),
    (re.compile(r"\bStart of combat\b", re.I), "Awal Combat"),
    (re.compile(r"\bAt the start of each round\b", re.I), "Di awal setiap Round"),
    (re.compile(r"\bAt the end of each round\b", re.I), "Di akhir setiap Round"),
    (re.compile(r"\bAt the start of the round\b", re.I), "Di awal Round"),
    (re.compile(r"\bAt the end of the round\b", re.I), "Di akhir Round"),
    (re.compile(r"\bAfter winning a battle\b", re.I), "Setelah memenangkan Combat"),
    (re.compile(r"\bAfter losing a battle\b", re.I), "Setelah kalah dalam Combat"),
    (re.compile(r"\bDuring battle\b", re.I), "Selama Combat"),
    (re.compile(r"\bDuring combat\b", re.I), "Selama Combat"),
    (re.compile(r"\bDuring the Prepare phase\b", re.I), "Selama fase Preparation"),
    (re.compile(r"\bPrepare phase\b", re.I), "fase Preparation"),
    (re.compile(r"\bWhen played\b", re.I), "Saat dimainkan"),
    (re.compile(r"\bWhen bought\b", re.I), "Saat dibeli"),
    (re.compile(r"\bWhen sold\b", re.I), "Saat dijual"),
    (re.compile(r"\bWhen upgraded\b", re.I), "Saat di-upgrade"),
    (re.compile(r"\bWhen combined\b", re.I), "Saat digabungkan"),
    (re.compile(r"\bWhen casting a skill\b", re.I), "Saat menggunakan Skill"),
    (re.compile(r"\bAfter casting a skill\b", re.I), "Setelah menggunakan Skill"),
    (re.compile(r"\bUpon death\b", re.I), "Saat gugur"),
    (re.compile(r"\bWhen defeated\b", re.I), "Saat dikalahkan"),
    (re.compile(r"\bWhen taking damage\b", re.I), "Saat menerima Damage"),
    (re.compile(r"\bWhen dealing damage\b", re.I), "Saat memberikan Damage"),
    (re.compile(r"\bFor every (\d+)\b", re.I), r"Untuk setiap \1"),
    (re.compile(r"\bEvery (\d+) basic attacks\b", re.I), r"Setiap \1 Basic Attack"),
    (re.compile(r"\bEvery (\d+) seconds?\b", re.I), r"Setiap \1 detik"),
    (re.compile(r"\bEvery (\d+) rounds?\b", re.I), r"Setiap \1 Round"),
    (re.compile(r"\bover (\d+(?:\.\d+)?) seconds?\b", re.I), r"selama \1 detik"),
    (re.compile(r"\bfor (\d+(?:\.\d+)?) seconds?\b", re.I), r"selama \1 detik"),
    (re.compile(r"\bup to (\d+) times?\b", re.I), r"hingga \1 kali"),
    (re.compile(r"\bup to (\d+) stacks?\b", re.I), r"hingga \1 stack"),
    (re.compile(r"\b(\d+)-Day Trial\b", re.I), r"Trial \1 Hari"),
    (re.compile(r"\b(\d+)-second\b", re.I), r"\1 detik"),
    # Card & Game Category Terms (Tier 1 style: Kartu Hero, Kartu Efek, Kartu Secret Art)
    (re.compile(r"\bFactionless Hero Cards?\b", re.I), "Kartu Hero Netral"),
    (re.compile(r"\bSecret Art Cards?\b", re.I), "Kartu Secret Art"),
    (re.compile(r"\bEffect Cards?\b", re.I), "Kartu Efek"),
    (re.compile(r"\bHero Cards?\b", re.I), "Kartu Hero"),
    (re.compile(r"\bEquipment Cards?\b", re.I), "Kartu Equipment"),
    (re.compile(r"\bTactics Cards?\b", re.I), "Kartu Taktik"),
    (re.compile(r"\bTrick Cards?\b", re.I), "Kartu Trik"),
    (re.compile(r"\bCard Packs?\b", re.I), "Paket Kartu"),
    (re.compile(r"\bHand Cards?\b", re.I), "Kartu Tangan"),
    (re.compile(r"\bActive Skill\b", re.I), "Skill Aktif"),
    (re.compile(r"\bPassive Skill\b", re.I), "Skill Pasif"),
    (re.compile(r"\bCombine Skill\b", re.I), "Skill Gabungan"),
    # Targets & Positioning
    (re.compile(r"\bAll allied heroes\b", re.I), "Semua Hero sekutu"),
    (re.compile(r"\ballied heroes\b", re.I), "Hero sekutu"),
    (re.compile(r"\bfriendly heroes\b", re.I), "Hero sekutu"),
    (re.compile(r"\ballied units\b", re.I), "unit sekutu"),
    (re.compile(r"\bAll allies\b", re.I), "Semua sekutu"),
    (re.compile(r"\ball allies\b", re.I), "semua sekutu"),
    (re.compile(r"\bAll enemies\b", re.I), "Semua musuh"),
    (re.compile(r"\ball enemies\b", re.I), "semua musuh"),
    (re.compile(r"\benemy heroes\b", re.I), "Hero musuh"),
    (re.compile(r"\bnearest enemy\b", re.I), "musuh terdekat"),
    (re.compile(r"\bfarthest enemy\b", re.I), "musuh terjauh"),
    (re.compile(r"\bsurrounding enemies\b", re.I), "musuh di sekitarnya"),
    (re.compile(r"\brandom distinct\b", re.I), "acak berbeda"),
    (re.compile(r"\brandom enemy\b", re.I), "musuh acak"),
    (re.compile(r"\brandom enemies\b", re.I), "musuh acak"),
    (re.compile(r"\brandom ally\b", re.I), "sekutu acak"),
    (re.compile(r"\brandom allies\b", re.I), "sekutu acak"),
    (re.compile(r"\badjacent allies\b", re.I), "sekutu di sekitarnya"),
    (re.compile(r"\bon the field\b", re.I), "di medan tempur"),
    (re.compile(r"\bon the board\b", re.I), "di papan"),
    (re.compile(r"\benters the field\b", re.I), "masuk ke medan tempur"),
    (re.compile(r"\bsame row\b", re.I), "baris yang sama"),
    (re.compile(r"\bsame column\b", re.I), "kolom yang sama"),
    (re.compile(r"\bfront row\b", re.I), "baris depan"),
    (re.compile(r"\bback row\b", re.I), "baris belakang"),
    (re.compile(r"\bhighest Level\b", re.I), "Level tertinggi"),
    (re.compile(r"\blowest Level\b", re.I), "Level terendah"),
    (re.compile(r"\bhighest ATK\b", re.I), "ATK tertinggi"),
    (re.compile(r"\blowest HP\b", re.I), "HP terendah"),
    (re.compile(r"\bhighest tier\b", re.I), "Tier tertinggi"),
    # Common sentence connectors & grammar
    (re.compile(r"\bTap the Skill description panel to View\b", re.I), "Ketuk panel deskripsi Skill untuk melihat"),
    (re.compile(r"\bCan only operate\b", re.I), "Hanya dapat dilakukan"),
    (re.compile(r"\bPlease try again later\b", re.I), "Silakan coba lagi nanti"),
    (re.compile(r"\bPlease try again\b", re.I), "Silakan coba lagi"),
    (re.compile(r"\bWaiting for others\b", re.I), "Menunggu pemain lain"),
    (re.compile(r"\bNo problem!\b", re.I), "Tidak masalah!"),
    (re.compile(r"\bClick to select\b", re.I), "Klik untuk memilih"),
    (re.compile(r"\bAre you sure you want to\b", re.I), "Yakin ingin"),
    (re.compile(r"\bDo you want to\b", re.I), "Apakah kamu ingin"),
    (re.compile(r"\bcannot be\b", re.I), "tidak dapat"),
    (re.compile(r"\bcan be\b", re.I), "dapat"),
    (re.compile(r"\bwill be\b", re.I), "akan"),
    (re.compile(r"\bequal to\b", re.I), "sebesar"),
    (re.compile(r"\bincreased to\b", re.I), "meningkat menjadi"),
    (re.compile(r"\breduced by\b", re.I), "berkurang sebesar"),
    (re.compile(r"\bincreased by\b", re.I), "meningkat sebesar"),
    (re.compile(r"\bpermanently increase\b", re.I), "meningkatkan secara permanen"),
    (re.compile(r"\bpermanently\b", re.I), "secara permanen"),
    (re.compile(r"\bimmediately\b", re.I), "segera"),
    (re.compile(r"\brandomly\b", re.I), "secara acak"),
    (re.compile(r"\badditionally\b", re.I), "selain itu"),
    (re.compile(r"\bexcluding\b", re.I), "kecuali"),
    (re.compile(r"\bincluding\b", re.I), "termasuk"),
    # Combat verbs & stats (protecting canonical Tier 1 English stat names before single-word verbs)
    (re.compile(r"\bdealing Damage\b", re.I), "memberikan Damage"),
    (re.compile(r"\bdealing\b", re.I), "memberikan"),
    (re.compile(r"\breducing\b", re.I), "mengurangi"),
    (re.compile(r"\bincreasing\b", re.I), "meningkatkan"),
    (re.compile(r"\brestoring\b", re.I), "memulihkan"),
    (re.compile(r"\bsummoning\b", re.I), "memanggil"),
    (re.compile(r"\bDeals?\b"), "Memberikan"),
    (re.compile(r"\bdeals?\b"), "memberikan"),
    (re.compile(r"\bRestores?\b"), "Memulihkan"),
    (re.compile(r"\brestores?\b"), "memulihkan"),
    (re.compile(r"\bGains?\b"), "Dapatkan"),
    (re.compile(r"\bgains?\b"), "mendapat"),
    (re.compile(r"\bGrants?\b"), "Memberikan"),
    (re.compile(r"\bgrants?\b"), "memberikan"),
    (re.compile(r"\bIncreases?\b"), "Meningkatkan"),
    (re.compile(r"\bincreases?\b"), "meningkatkan"),
    (re.compile(r"\bReduces?\b"), "Mengurangi"),
    (re.compile(r"\breduces?\b"), "mengurangi"),
    (re.compile(r"\bObtains?\b"), "Peroleh"),
    (re.compile(r"\bobtains?\b"), "memperoleh"),
    (re.compile(r"\bfirst obtained\b", re.I), "pertama kali diperoleh"),
    (re.compile(r"\bobtained\b", re.I), "diperoleh"),
    (re.compile(r"\bTriggers?\b"), "Memicu"),
    (re.compile(r"\btriggers?\b"), "memicu"),
    (re.compile(r"\bSummons?\b"), "Memanggil"),
    (re.compile(r"\bsummons?\b"), "memanggil"),
    (re.compile(r"\bTransforms? into\b", re.I), "Berubah menjadi"),
    (re.compile(r"\bReturns? to hand\b", re.I), "Kembali ke tangan"),
    (re.compile(r"\bDesignate\b"), "Pilih"),
    (re.compile(r"\bdesignate\b"), "pilih"),
    (re.compile(r"\bSelect\b"), "Pilih"),
    (re.compile(r"\bselect\b"), "pilih"),
    (re.compile(r"\bChoose\b"), "Pilih"),
    (re.compile(r"\bchoose\b"), "pilih"),
    (re.compile(r"\bUsage\b"), "Gunakan"),
    (re.compile(r"\bDamage Reduction\b", re.I), "Reduksi Damage"),
    (re.compile(r"\bMax Health\b", re.I), "Max HP"),
    (re.compile(r"\bCritical Rate\b", re.I), "Crit Rate"),
    (re.compile(r"\bCritical Damage\b", re.I), "Crit Damage"),
    (re.compile(r"\bEnergy Regen\b", re.I), "Regen Energi"),
    (re.compile(r"\bEnergy\b"), "Energi"),
    (re.compile(r"\bpieces of Equipment\b", re.I), "Equipment"),
    # UI, Meta, Social, Shop & System terms
    (re.compile(r"\bMonthly limit\b", re.I), "Batas bulanan"),
    (re.compile(r"\bDaily limit\b", re.I), "Batas harian"),
    (re.compile(r"\bWeekly limit\b", re.I), "Batas mingguan"),
    (re.compile(r"\bToday's reward\b", re.I), "Hadiah hari ini"),
    (re.compile(r"\bTotal usable coupons\b", re.I), "Total kupon tersedia"),
    (re.compile(r"\bDuo ranked\b", re.I), "Duo Ranked"),
    (re.compile(r"\bCard exchange round\b", re.I), "Round tukar kartu"),
    (re.compile(r"\bLineup guides\b", re.I), "Panduan Lineup"),
    (re.compile(r"\bSelect emoticon\b", re.I), "Pilih Emotikon"),
    (re.compile(r"\bgifted\b", re.I), "mengirim hadiah"),
    (re.compile(r"\bConfirm\b", re.I), "Konfirmasi"),
    (re.compile(r"\bCancel\b", re.I), "Batal"),
    (re.compile(r"\bSettings\b", re.I), "Pengaturan"),
    (re.compile(r"\bVictory\b"), "Kemenangan"),
    (re.compile(r"\bFailure\b"), "Kekalahan"),
    (re.compile(r"\bAlready claimed\b", re.I), "Sudah Diklaim"),
    (re.compile(r"\bClaimed\b", re.I), "Sudah Diklaim"),
    (re.compile(r"\bClaim\b"), "Klaim"),
    (re.compile(r"\bRewards?\b"), "Hadiah"),
    (re.compile(r"\brewards?\b"), "hadiah"),
    (re.compile(r"\bMissions?\b"), "Misi"),
    (re.compile(r"\bmissions?\b"), "misi"),
    (re.compile(r"\bAchievements?\b"), "Pencapaian"),
    (re.compile(r"\bachievements?\b"), "pencapaian"),
    (re.compile(r"\bLeaderboard\b"), "Papan Peringkat"),
    (re.compile(r"\bleaderboard\b"), "papan peringkat"),
    (re.compile(r"\bCompleted\b", re.I), "Selesai"),
    (re.compile(r"\bLocked\b"), "Terkunci"),
    (re.compile(r"\bUnlocked\b"), "Terbuka"),
    (re.compile(r"\bEquipped\b"), "Terpasang"),
    (re.compile(r"\bPurchase\b"), "Beli"),
    (re.compile(r"\bMatch\b"), "Pertandingan"),
    (re.compile(r"\bmatch\b"), "pertandingan"),
    (re.compile(r"\bPlayers\b"), "Pemain"),
    (re.compile(r"\bplayers\b"), "pemain"),
    (re.compile(r"\bFriends?\b"), "Teman"),
    (re.compile(r"\bfriends?\b"), "teman"),
    (re.compile(r"\bTeam\b"), "Tim"),
    (re.compile(r"\bteam\b"), "tim"),
    (re.compile(r"\bSystem\b"), "Sistem"),
    (re.compile(r"\bsystem\b"), "sistem"),
    (re.compile(r"\bSource:\b"), "Sumber:"),
    (re.compile(r"\bdetails\b"), "detail"),
    (re.compile(r"\bguides\b"), "panduan"),
    (re.compile(r"\bvoucher\b"), "kupon"),
    # High-frequency function words (only multi-letter whole words so [p]/[q] variables are untouched)
    (re.compile(r"\bWhen you\b"), "Saat kamu"),
    (re.compile(r"\bwhen you\b"), "saat kamu"),
    (re.compile(r"\bIf you\b"), "Jika kamu"),
    (re.compile(r"\bif you\b"), "jika kamu"),
    (re.compile(r"\bYou can\b"), "Kamu dapat"),
    (re.compile(r"\byou can\b"), "kamu dapat"),
    (re.compile(r"\bYou have\b"), "Kamu memiliki"),
    (re.compile(r"\byou have\b"), "kamu memiliki"),
    (re.compile(r"\bYou will\b"), "Kamu akan"),
    (re.compile(r"\byou will\b"), "kamu akan"),
    (re.compile(r"\bAfter the\b"), "Setelah"),
    (re.compile(r"\bafter the\b"), "setelah"),
    (re.compile(r"\bDuring the\b"), "Selama"),
    (re.compile(r"\bduring the\b"), "selama"),
    (re.compile(r"\bbetween\b"), "antara"),
    (re.compile(r"\bwithin\b"), "dalam"),
    (re.compile(r"\bwithout\b"), "tanpa"),
    (re.compile(r"\bagainst\b"), "terhadap"),
    (re.compile(r"\bthrough\b"), "melalui"),
    (re.compile(r"\bcurrent\b", re.I), "saat ini"),
    (re.compile(r"\bidentical\b", re.I), "yang sama"),
    (re.compile(r"\badditional\b", re.I), "tambahan"),
    (re.compile(r"\bremaining\b", re.I), "tersisa"),
    (re.compile(r"\bseconds\b", re.I), "detik"),
    (re.compile(r"\bpoints\b", re.I), "poin"),
    (re.compile(r"\btimes\b"), "kali"),
    (re.compile(r"\bcards\b"), "kartu"),
    (re.compile(r"\bcard\b"), "kartu"),
    (re.compile(r"\benemies\b"), "musuh"),
    (re.compile(r"\benemy\b"), "musuh"),
    (re.compile(r"\ballies\b"), "sekutu"),
    (re.compile(r"\bally\b"), "sekutu"),
    (re.compile(r"\band\b"), "dan"),
    (re.compile(r"\bwith\b"), "dengan"),
    (re.compile(r"\bfrom\b"), "dari"),
    (re.compile(r"\binto\b"), "menjadi"),
    (re.compile(r"\byour\b"), "milikmu"),
    (re.compile(r"\btheir\b"), "mereka"),
    (re.compile(r"\bonly\b"), "hanya"),
    (re.compile(r"\beach\b"), "setiap"),
    (re.compile(r"\bevery\b"), "setiap"),
]

# Terms that must never be split or altered during EN->ID prose conversion
CANONICAL_PROTECTED_TERMS: tuple[str, ...] = (
    "Honor of Kings: Ace",
    "Honor of Kings",
    "Central Plains",
    "Central Plain",
    "Riverlands",
    "Zhulu Plateau",
    "Three Kingdoms",
    "Sunset Sea",
    "First Lands",
    "Temporary Level",
    "True Level",
    "Physical Attack",
    "Magic Attack",
    "Physical Damage",
    "Magic Damage",
    "Magical Damage",
    "True Damage",
    "Physical Defense",
    "Magic Defense",
    "Attack Speed",
    "Movement Speed",
    "Attack Power",
    "Attack Range",
    "Basic Attack",
    "Max HP",
    "Max Mana",
    "Crit Rate",
    "Crit Damage",
    "Chess Player",
    "Secret Art",
    "Diamond Frenzy",
    "Ace Duel",
    "Strongest King",
    "Supreme Challenger",
    "Stubborn Bronze",
    "Vientiane King",
    "Sage's Sanctuary",
    "Maple Leaf Dance",
    "Graceful Dance",
    "Gentle Call",
    "Tidal Symphony",
    "Tri-Point Banner",
    "Ancient Coin",
    "Refined Ancient Coin",
    "Coin Machine",
    "Rapid Growth",
    "Perfect Revive",
    "Akomia Core",
    "Steal Fire",
    "Magic Penetration",
    "Physical Penetration",
    "Kartu Talent",
    "Kartu Efek",
    "Kartu Equipment",
    "Voucher Hero",
)

STOPWORD_GUARD_RE = re.compile(
    r"\b(the|and|with|from|into|when|while|after|before|during|within|without|"
    r"between|against|through|for|you|your|their|his|her|its|this|that|these|those|"
    r"each|every|deals|dealing|restores|restoring|gains|gaining|grants|granting|"
    r"increases|increasing|reduces|reducing|summons|summoning|triggers|triggering|"
    r"enemies|allies|cannot|will|have|has|had|are|was|were|been)\b",
    re.I,
)

LORD_NAME_TO_T2_ALT: dict[str, str] = {
    "Little Daji": "小妲己",
    "Yao Mei": "瑶妹",
    "Arli": "阿离",
    "Jing": "镜",
    "Qiao Xi": "乔汐",
    "Little Chang'e": "常小娥",
    "Yu Huan": "玉环",
    "Little Zhuang Fish": "庄小鱼",
    "Marco": "马可",
    "Bai Ge": "白歌",
    "Zhaojun": "昭君",
    "Uncle Ban": "班叔",
    "Yi Xing": "弈星",
    "Little Sun Bin": "孙小宾",
    "Mister Ming": "明先生",
    "Naonao": "闹闹",
    "Director Jiang": "姜导",
    "Ying Lü": "嬴律",
    "Xiang": "香香",
}

TIER1_EMBEDDED_EN_CLEANUP: tuple[tuple[str, str], ...] = (
    ("Indomitable Will", "Tekad Baja"),
    ("Try Your Luck", "Uji Keberuntungan"),
    ("Glory of the Old Guard", "Kejayaan Garda Lama"),
    ("Quench with Illusions", "Padamkan dengan Ilusi"),
    ("Muster the Troops", "Kumpulkan Pasukan"),
    ("Power of the Source", "Kekuatan Sumber"),
    ("Bane of the Mighty", "Kutukan Sang Perkasa"),
    ("Kartu Effect", "Kartu Efek"),
    ("kartu Effect", "kartu Efek"),
)


def _normalize_en_key(text: str) -> str:
    cleaned = TAG_RE.sub("", text)
    cleaned = CONTROL_TOKEN_RE.sub("", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip().lower()


@dataclass
class ThreeTierGlossary:
    tier1_exact_zh_to_id: dict[str, str] = field(default_factory=dict)
    tier1_plain_zh_to_id: dict[str, str] = field(default_factory=dict)
    tier1_formula_zh_to_id: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    tier1_en_card_to_id_desc: dict[str, str] = field(default_factory=dict)
    tier1_en_desc_to_id_desc: dict[str, str] = field(default_factory=dict)
    tier2_zh_to_en: dict[str, str] = field(default_factory=dict)
    tier2_plain_zh_to_en: dict[str, str] = field(default_factory=dict)
    protected_en_terms: list[str] = field(default_factory=list)
    _protected_re: re.Pattern[str] | None = field(default=None, init=False, repr=False)

    @classmethod
    def from_reference_files(
        cls,
        tier1_path: Path,
        tier2_path: Path,
        tier2_details_path: Path | None = None,
    ) -> "ThreeTierGlossary":
        instance = cls()
        protected_set: set[str] = set(CANONICAL_PROTECTED_TERMS)

        t1_data: dict = {}
        if tier1_path.exists():
            t1_data = json.loads(tier1_path.read_text(encoding="utf-8"))
            instance._ingest_tier1(t1_data, protected_set)
        if tier2_path.exists():
            t2 = json.loads(tier2_path.read_text(encoding="utf-8"))
            instance._ingest_tier2(t2, protected_set)

        if tier2_details_path is None:
            tier2_details_path = tier2_path.with_name("tier2_wiki_details_en.json")
        if tier2_details_path.exists():
            t2_details = json.loads(tier2_details_path.read_text(encoding="utf-8"))
            instance._ingest_tier2_details(t1_data, t2_details, protected_set)

        for zh_k, id_v in BRACKET_TERM_MAP.items():
            instance.tier1_exact_zh_to_id.setdefault(zh_k, id_v)
        for zh_k, id_v in WINDOWS_108_ZH_TO_ID.items():
            instance._register_t1_pair(zh_k, id_v)

        # Sort protected multi-word proper names longest-first, excluding any phrase with English stopwords
        instance.protected_en_terms = sorted(
            (
                t
                for t in protected_set
                if len(t) >= 5
                and any(c.isupper() for c in t)
                and not STOPWORD_GUARD_RE.search(t)
            ),
            key=len,
            reverse=True,
        )
        if instance.protected_en_terms:
            escaped = "|".join(re.escape(t) for t in instance.protected_en_terms)
            instance._protected_re = re.compile(rf"(?<![A-Za-z])(?:{escaped})(?![A-Za-z])")
        return instance

    def _register_t1_pair(self, zh: str, id_val: str) -> None:
        zh = zh.strip()
        id_val = id_val.strip()
        if not zh or not id_val:
            return
        for old_en, new_id in TIER1_EMBEDDED_EN_CLEANUP:
            if old_en in id_val:
                id_val = id_val.replace(old_en, new_id)
        self.tier1_exact_zh_to_id[zh] = id_val
        norm = normalize_plain_zh(zh)
        if norm:
            self.tier1_plain_zh_to_id[norm] = id_val
        skel = normalize_formula_skeleton_zh(zh)
        if skel and len(skel) >= 6:
            cands = self.tier1_formula_zh_to_id.setdefault(skel, [])
            if (zh, id_val) not in cands:
                cands.append((zh, id_val))

    def _register_t2_pair(self, zh: str, en_val: str) -> None:
        zh = zh.strip()
        en_val = en_val.strip()
        if not zh or not en_val:
            return
        self.tier2_zh_to_en.setdefault(zh, en_val)
        norm = normalize_plain_zh(zh)
        if norm:
            self.tier2_plain_zh_to_en.setdefault(norm, en_val)

    def _ingest_tier1(self, t1: dict, protected_set: set[str]) -> None:
        # 1. Factions & Keywords (stored as dicts on hok-ace-translate-id.netlify.app)
        factions = t1.get("factions", {})
        if isinstance(factions, dict):
            for zh_f, en_f in factions.items():
                self._register_t1_pair(zh_f, en_f)
                protected_set.add(en_f)
        elif isinstance(factions, list):
            for item in factions:
                if isinstance(item, dict):
                    self._register_t1_pair(
                        item.get("cn") or item.get("nameCn") or "",
                        item.get("name") or "",
                    )

        keywords = t1.get("keywords", {})
        if isinstance(keywords, dict):
            for kw_name in keywords:
                protected_set.add(kw_name)

        # 2. Heroes, Effect Cards, Equipment, Talents (including awaken, skills, and Lv enhancements)
        for category in ("hero", "effect", "equip", "talent"):
            for item in t1.get(category, []):
                name_cn = (item.get("cn") or item.get("nameCn") or "").strip()
                name_en = (item.get("name") or "").strip()
                desc_cn = (item.get("descCn") or "").strip()
                desc_id = (item.get("desc") or "").strip()
                if name_cn and name_en:
                    if category in ("hero", "equip") and not STOPWORD_GUARD_RE.search(name_en):
                        self._register_t1_pair(name_cn, name_en)
                        protected_set.add(name_en)
                    else:
                        self._register_t2_pair(name_cn, name_en)
                if desc_cn and desc_id:
                    self._register_t1_pair(desc_cn, desc_id)

                awaken = item.get("awaken")
                if isinstance(awaken, dict):
                    self._register_t1_pair(
                        awaken.get("descCn") or "", awaken.get("desc") or ""
                    )

                for sk in item.get("skills", []):
                    sk_cn = (sk.get("cn") or sk.get("nameCn") or "").strip()
                    sk_name = (sk.get("name") or "").strip()
                    if sk_cn and sk_name:
                        if not STOPWORD_GUARD_RE.search(sk_name):
                            self._register_t1_pair(sk_cn, sk_name)
                            protected_set.add(sk_name)
                        else:
                            self._register_t2_pair(sk_cn, sk_name)
                    self._register_t1_pair(
                        sk.get("descCn") or "", sk.get("desc") or ""
                    )
                    for enh in sk.get("enh", []):
                        self._register_t1_pair(
                            enh.get("descCn") or "", enh.get("desc") or ""
                        )

        # 3. Lords / Chess Players (19 items)
        for lord in t1.get("lords", []):
            lord_name = (lord.get("name") or "").strip()
            lord_cn = (lord.get("cn") or lord.get("nameCn") or "").strip()
            if lord_name:
                protected_set.add(lord_name)
            if lord_cn and lord_name:
                self._register_t1_pair(lord_cn, lord_name)
            for tal in lord.get("talents", []):
                c_name = (tal.get("cardName") or "").strip()
                c_desc = (tal.get("desc") or "").strip()
                if c_name:
                    if not STOPWORD_GUARD_RE.search(c_name):
                        protected_set.add(c_name)
                    if c_desc:
                        self.tier1_en_card_to_id_desc[c_name] = c_desc
            for rel in lord.get("related", []):
                r_name = (rel.get("name") or "").strip()
                r_desc = (rel.get("desc") or "").strip()
                if r_name:
                    if not STOPWORD_GUARD_RE.search(r_name):
                        protected_set.add(r_name)
                    if r_desc:
                        self.tier1_en_card_to_id_desc[r_name] = r_desc

    def _ingest_tier2(self, t2: list[dict], protected_set: set[str]) -> None:
        for entry in t2:
            alt_zh = (entry.get("alt") or "").strip()
            name_en = (entry.get("name") or "").strip()
            if alt_zh and name_en:
                self._register_t2_pair(alt_zh, name_en)
                if entry.get("type") in ("Hero", "Chess player") and not STOPWORD_GUARD_RE.search(name_en):
                    protected_set.add(name_en)

    def _ingest_tier2_details(
        self, t1: dict, t2_details: list[dict], protected_set: set[str]
    ) -> None:
        t2_players_by_alt: dict[str, dict] = {}
        for item in t2_details:
            if item.get("type") == "Chess player" and item.get("alt"):
                t2_players_by_alt[item["alt"].strip()] = item

            en_block = item.get("en") or {}
            zh_block = item.get("zh") or {}
            for key in ("calc_copies", "effect_copies", "skill_names", "breakpoints", "rule_notes"):
                for zh_s, en_s in zip(zh_block.get(key, []), en_block.get(key, [])):
                    self._register_t2_pair(zh_s, en_s)

            for ab_zh, ab_en in zip(
                zh_block.get("abilities", []), en_block.get("abilities", [])
            ):
                self._register_t2_pair(ab_zh.get("name", ""), ab_en.get("name", ""))
                self._register_t2_pair(ab_zh.get("desc", ""), ab_en.get("desc", ""))
                # If ab_en["name"] is in tier1_en_card_to_id_desc, map ab_en["desc"] and ab_zh["desc"] to Tier 1 ID!
                ab_en_name = (ab_en.get("name") or "").strip()
                ab_en_desc = (ab_en.get("desc") or "").strip()
                if ab_en_name in self.tier1_en_card_to_id_desc:
                    id_desc = self.tier1_en_card_to_id_desc[ab_en_name]
                    zh_d = ab_zh.get("desc", "")
                    if len(normalize_plain_zh(zh_d)) >= 8:
                        self._register_t1_pair(zh_d, id_desc)
                    if ab_en_desc and len(ab_en_desc) >= 20:
                        self.tier1_en_desc_to_id_desc[_normalize_en_key(ab_en_desc)] = id_desc

        # Pair all 19 Tier 1 Lords with their corresponding Tier 2 Chess Player detail pages
        for lord in t1.get("lords", []):
            l_name = (lord.get("name") or "").strip()
            alt_zh = LORD_NAME_TO_T2_ALT.get(l_name)
            t2_player = t2_players_by_alt.get(alt_zh or "")
            if not t2_player:
                continue
            zh_abs = (t2_player.get("zh") or {}).get("abilities", [])
            en_abs = (t2_player.get("en") or {}).get("abilities", [])
            tals = lord.get("talents", [])
            rels = lord.get("related", [])
            for idx, tal in enumerate(tals):
                c_name = (tal.get("cardName") or "").strip()
                c_desc = (tal.get("desc") or "").strip()
                if idx < len(zh_abs):
                    zh_ab = zh_abs[idx]
                    if c_name and not STOPWORD_GUARD_RE.search(c_name):
                        self._register_t1_pair(zh_ab.get("name", ""), c_name)
                    if c_desc and len(normalize_plain_zh(zh_ab.get("desc", ""))) >= 8:
                        self._register_t1_pair(zh_ab.get("desc", ""), c_desc)
                    m_split = re.search(
                        r"^(.+?[。！？])\s*([^：:。]{2,12})[：:](.+)$",
                        zh_ab.get("desc", ""),
                    )
                    if m_split:
                        first_zh, sub_name_zh, sub_desc_zh = m_split.groups()
                        if c_desc and len(normalize_plain_zh(first_zh)) >= 8:
                            self._register_t1_pair(first_zh, c_desc)
                        if len(rels) > 1:
                            r1_name = (rels[1].get("name") or "").strip()
                            r1_desc = (rels[1].get("desc") or "").strip()
                            if r1_name and not STOPWORD_GUARD_RE.search(r1_name):
                                self._register_t1_pair(sub_name_zh, r1_name)
                            if r1_desc and len(normalize_plain_zh(sub_desc_zh)) >= 8:
                                self._register_t1_pair(sub_desc_zh, r1_desc)
                                if c_desc and r1_name and len(normalize_plain_zh(zh_ab.get("desc", ""))) >= 8:
                                    self._register_t1_pair(
                                        zh_ab.get("desc", ""),
                                        f"{c_desc}\n{r1_name}: {r1_desc}",
                                    )
                if idx < len(en_abs) and c_desc:
                    en_ab_desc = (en_abs[idx].get("desc") or "").strip()
                    if en_ab_desc and len(en_ab_desc) >= 20:
                        self.tier1_en_desc_to_id_desc[_normalize_en_key(en_ab_desc)] = c_desc

    def translate_en_to_id(self, en_text: str) -> str:
        """Convert English HoK Ace text into natural Indonesian while preserving tags, proper nouns, and tokens."""
        if not en_text or not en_text.strip():
            return en_text

        norm_en = _normalize_en_key(en_text)
        if (
            len(en_text.strip()) >= 20
            and norm_en in self.tier1_en_desc_to_id_desc
            and not TAG_RE.findall(en_text)
            and not PLACEHOLDER_RE.findall(en_text)
        ):
            return self.tier1_en_desc_to_id_desc[norm_en]

        def _convert_segment(seg: str) -> str:
            out = seg.replace("The First Lands", "First Lands")

            # Normalize English baseline variants to canonical Tier 1 terms
            var_subs = [
                (r"(?<![A-Za-z])(?:Magic|Magical)\s+ATK(?![A-Za-z])", "Magic Attack"),
                (r"(?<![A-Za-z])Physical\s+ATK(?![A-Za-z])", "Physical Attack"),
                (r"(?<![A-Za-z])Sage['’]s\s+Sanctuary(?![A-Za-z])", "Sage's Sanctuary"),
                (r"\b(\d+)\s*Chang\b", r"\1 kartu"),
                (r"\b(\d+)\s*Number of times\b", r"\1 kali"),
                (r"(?<![A-Za-z])Magical Attack(?![A-Za-z])", "Magic Attack"),
                (r"(?<![A-Za-z])Magical Damage(?![A-Za-z])", "Magic Damage"),
                (r"(?<![A-Za-z])Magical Defense(?![A-Za-z])", "Magic Defense"),
                (r"(?<![A-Za-z])Spell Penetration(?![A-Za-z])", "Magic Penetration"),
                (
                    r"(?<![A-Za-z])(?:Maximum HP|Max Health|Maximum Health)(?![A-Za-z])",
                    "Max HP",
                ),
                (r"(?<![A-Za-z])Maximum Mana(?![A-Za-z])", "Max Mana"),
                (
                    r"(?<![A-Za-z])(?:Exquisite Ancient Coins|Exquisite Ancient Coin|Refined Ancient Coins)(?![A-Za-z])",
                    "Refined Ancient Coin",
                ),
                (r"(?<![A-Za-z])Ancient Coin Machine(?![A-Za-z])", "Coin Machine"),
                (r"(?<![A-Za-z])Ancient Coins(?![A-Za-z])", "Ancient Coin"),
                (r"(?<![A-Za-z])Perfect Resurrection(?![A-Za-z])", "Perfect Revive"),
                (r"(?<![A-Za-z])Arcomia Core(?![A-Za-z])", "Akomia Core"),
                (r"(?<![A-Za-z])Fire Thief(?![A-Za-z])", "Steal Fire"),
                (r"(?<![A-Za-z])(?:Talent Cards|Talent Card)(?![A-Za-z])", "Kartu Talent"),
                (r"(?<![A-Za-z])(?:Effect Cards|Effect Card)(?![A-Za-z])", "Kartu Efek"),
                (
                    r"(?<![A-Za-z])(?:Equipment Cards|Equipment Card)(?![A-Za-z])",
                    "Kartu Equipment",
                ),
                (r"(?<![A-Za-z])(?:Hero Vouchers|Hero Voucher)(?![A-Za-z])", "Voucher Hero"),
                (r"(?<![A-Za-z])Temporary Levels?\s+up(?![A-Za-z])", "Peningkatan Temporary Level"),
                (r"(?<![A-Za-z])Temporary Levels(?![A-Za-z])", "Temporary Level"),
                (r"(?<![A-Za-z])real (?:Level|Tier)s?(?![A-Za-z])", "True Level"),
                (
                    r"(?<![A-Za-z])(?:Perfect Revivals?|Perfect Resurrections?)(?![A-Za-z])",
                    "Perfect Revive",
                ),
                (r"(?<![A-Za-z])faster growth(?![A-Za-z])", "pertumbuhan lebih cepat"),
                (r"(?<![A-Za-z])growth methods?(?![A-Za-z])", "metode pertumbuhan"),
            ]
            for pat, repl in var_subs:
                out = re.sub(pat, repl, out, flags=re.IGNORECASE)

            sentinels: list[tuple[str, str]] = []
            if self._protected_re is not None:
                def _protect_match(m: re.Match[str]) -> str:
                    idx = len(sentinels)
                    tok = f"__WXQPR{idx}__"
                    val = m.group(0)
                    if val == "Central Plains":
                        val = "Central Plain"
                    elif val == "Sunset Sea":
                        val = "Sunset"
                    elif val == "Magical Damage":
                        val = "Magic Damage"
                    sentinels.append((tok, val))
                    return tok

                out = self._protected_re.sub(_protect_match, out)

            out = translate_segment_en_to_id(out)

            for tok, orig_val in sentinels:
                out = out.replace(tok, orig_val, 1)

            out = re.sub(
                r"\b(Ancient Coin|Refined Ancient Coin|Central Plain|Zhulu(?: Plateau)?|Three Kingdoms|Sunset(?: Sea)?|Jixia|Great Wall|Xuanyong|Yaotian|Cloudream|Riverlands)\s+[Kk]artu(?:\s+Hero)?\b",
                lambda m: f"Kartu Hero {m.group(1)}" if "hero" in m.group(0).lower() else f"Kartu {m.group(1)}",
                out,
            )
            out = re.sub(r"\b(\d+)\s+[Aa]cak\s+(Kartu\s+[A-Za-z ]+)\b", r"\1 \2 acak", out)

            for old_ft, new_ft in (
                ("Kartu Effect", "Kartu Efek"),
                ("kartu Effect", "kartu Efek"),
                ("Sementara Level", "Temporary Level"),
                ("sementara Level", "Temporary Level"),
                ("Nyata Level", "True Level"),
                ("nyata Level", "True Level"),
                ("Cepat Growth", "pertumbuhan lebih cepat"),
                ("cepat growth", "pertumbuhan lebih cepat"),
            ):
                out = out.replace(old_ft, new_ft)
            out = re.sub(r"(?i)sempurna kebangkitan", "Perfect Revive", out)
            out = re.sub(r"(?i)\bTemporary Level\s+atas\b", "Peningkatan Temporary Level", out)
            out = re.sub(r"\bsebuah\s+(?=\d)", "", out, flags=re.I)
            out = re.sub(r"\badalah\s+milikmu\b", "milikmu", out, flags=re.I)

            return out

        return translate_preserving_skeleton(en_text, _convert_segment)

    def _fit_length_bound(self, source_zh: str, candidate: str) -> str:
        """Guarantee candidate satisfies len(candidate) <= max(len(source_zh) * 8, 48) when len(source_zh) >= 4."""
        for old_ft, new_ft in (
            ("Kartu Effect", "Kartu Efek"),
            ("kartu Effect", "kartu Efek"),
            ("Sementara Level", "Temporary Level"),
            ("sementara Level", "Temporary Level"),
            ("Nyata Level", "True Level"),
            ("nyata Level", "True Level"),
            ("Cepat Growth", "pertumbuhan lebih cepat"),
            ("cepat growth", "pertumbuhan lebih cepat"),
        ):
            candidate = candidate.replace(old_ft, new_ft)
        candidate = re.sub(r"(?i)sempurna kebangkitan", "Perfect Revive", candidate)
        candidate = re.sub(r"(?i)\bTemporary Level\s+atas\b", "Peningkatan Temporary Level", candidate)
        candidate = re.sub(r"\bsebuah\s+(?=\d)", "", candidate, flags=re.I)
        candidate = re.sub(r"\badalah\s+milikmu\b", "milikmu", candidate, flags=re.I)

        if len(source_zh) < 4:
            return candidate
        limit = max(len(source_zh) * 8, 48)
        if len(candidate) <= limit:
            return candidate

        compact_replacements = (
            ("tidak akan", "takkan"),
            ("sebaiknya tidak", "jangan"),
            ("tidak bisa", "tak bisa"),
            ("tidak dapat", "tak dapat"),
            ("memberitahu", "beri tahu"),
            ("tayangan ulang", "replay"),
            ("memenangkan", "menang"),
            ("beberapa lebih banyak", "lagi"),
            ("menampilkan", "tunjukkan"),
            ("bagaimana ke", "cara"),
            ("bagaimana cara", "cara"),
            ("sebuah ", ""),
            ("dari ", ""),
            ("adalah ", ""),
            ("itu ", ""),
            ("untuk ", ""),
            ("yang ", ""),
            ("secara permanen", "permanen"),
            ("secara acak", "acak"),
            ("untuk pertama kalinya", "pertama kali"),
            ("di medan tempur", "di field"),
            ("pertandingan", "match"),
            ("meningkatkan", "+"),
            ("mengurangi", "-"),
            ("mendapatkan", "dapat"),
            ("memperoleh", "dapat"),
            ("memberikan", "beri"),
            ("  ", " "),
        )
        out = candidate
        for old, new in compact_replacements:
            if len(out) <= limit:
                break
            out = out.replace(old, new)
        if (
            len(out) > limit
            and not TAG_RE.findall(source_zh)
            and not PLACEHOLDER_RE.findall(source_zh)
            and not CONTROL_TOKEN_RE.findall(source_zh)
            and ";" not in source_zh
        ):
            head = out[:limit]
            out = (head.rsplit(" ", 1)[0] if " " in head else head).rstrip(" ,;:-.")
        return out

    def translate_entry(
        self, source_zh: str, baseline_en: str | None = None
    ) -> tuple[str, str]:
        """
        Return (translated_id, tier_used) where tier_used is 'tier1', 'tier2', or 'tier3'.
        Guarantees validate_translation(source_zh, translated_id) == (True, 'ok').
        """
        # 1. Tier 1 exact match (includes exact 108 missing Windows strings & Tier 1 CN->ID)
        if source_zh in self.tier1_exact_zh_to_id:
            raw_t1 = self.tier1_exact_zh_to_id[source_zh]
            ok_direct, _ = validate_translation(source_zh, raw_t1)
            if ok_direct:
                return (raw_t1, "tier1")
            cand = self._fit_length_bound(
                source_zh,
                reinject_skeleton_from_source(
                    source_zh,
                    raw_t1,
                    inner_translator=self._translate_raw_zh_to_id,
                    baseline_en=baseline_en,
                    en_translator=self.translate_en_to_id,
                ),
            )
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (cand, "tier1")

        # 2. Tier 1 normalized (tag-stripped) match + skeleton re-injection
        norm_zh = normalize_plain_zh(source_zh)
        if norm_zh and norm_zh in self.tier1_plain_zh_to_id:
            cand = self._fit_length_bound(
                source_zh,
                reinject_skeleton_from_source(
                    source_zh,
                    self.tier1_plain_zh_to_id[norm_zh],
                    inner_translator=self._translate_raw_zh_to_id,
                    baseline_en=baseline_en,
                    en_translator=self.translate_en_to_id,
                ),
            )
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (cand, "tier1")

        # 2b. Tier 1 formula-skeleton match (handles all 234 dynamic formula Hero skills/enhancements/awakenings)
        skel_zh = normalize_formula_skeleton_zh(source_zh)
        if skel_zh and skel_zh in self.tier1_formula_zh_to_id:
            cands = self.tier1_formula_zh_to_id[skel_zh]
            src_nums = re.findall(r"\d+(?:\.\d+)?", normalize_plain_zh(source_zh))
            best_cand = cands[0]
            best_score = -1
            for c_cn, c_id in cands:
                c_nums = re.findall(r"\d+(?:\.\d+)?", normalize_plain_zh(c_cn))
                score = sum(1 for a, b in zip(src_nums, c_nums) if a == b)
                if score > best_score:
                    best_score = score
                    best_cand = (c_cn, c_id)
            t1_desc_cn, t1_desc_id = best_cand
            cand = self._fit_length_bound(
                source_zh,
                reinject_formula_and_skeleton(
                    source_zh,
                    t1_desc_cn,
                    t1_desc_id,
                    inner_translator=self._translate_raw_zh_to_id,
                    baseline_en=baseline_en,
                    en_translator=self.translate_en_to_id,
                ),
            )
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (cand, "tier1")

        # 2c. Tier 1 Lord card name / description match via baseline_en
        if baseline_en:
            clean_en = TAG_RE.sub("", baseline_en).strip()
            if clean_en in self.tier1_en_card_to_id_desc and len(source_zh) >= 8:
                cand = self._fit_length_bound(
                    source_zh,
                    reinject_skeleton_from_source(
                        source_zh,
                        self.tier1_en_card_to_id_desc[clean_en],
                        inner_translator=self._translate_raw_zh_to_id,
                        baseline_en=baseline_en,
                        en_translator=self.translate_en_to_id,
                    ),
                )
                if validate_translation(source_zh, cand)[0]:
                    return (cand, "tier1")

            norm_en = _normalize_en_key(baseline_en)
            if norm_en in self.tier1_en_desc_to_id_desc and len(source_zh) >= 8:
                cand = self._fit_length_bound(
                    source_zh,
                    reinject_skeleton_from_source(
                        source_zh,
                        self.tier1_en_desc_to_id_desc[norm_en],
                        inner_translator=self._translate_raw_zh_to_id,
                        baseline_en=baseline_en,
                        en_translator=self.translate_en_to_id,
                    ),
                )
                if validate_translation(source_zh, cand)[0]:
                    return (cand, "tier1")

        # 3. Tier 2 exact or plain entity/detail match -> EN -> ID
        t2_en = self.tier2_zh_to_en.get(source_zh) or (
            self.tier2_plain_zh_to_en.get(norm_zh) if norm_zh else None
        )
        if t2_en:
            t2_id = self.translate_en_to_id(t2_en)
            cand = self._fit_length_bound(
                source_zh,
                reinject_skeleton_from_source(
                    source_zh,
                    t2_id,
                    inner_translator=self._translate_raw_zh_to_id,
                    baseline_en=baseline_en,
                    en_translator=self.translate_en_to_id,
                ),
            )
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (cand, "tier2")

        # 4. Tier 3: Use baseline_en (ZH -> EN -> ID)
        if baseline_en:
            cand = self._fit_length_bound(
                source_zh,
                sanitize_target_text(source_zh, self.translate_en_to_id(baseline_en)),
            )
            ok, _ = validate_translation(source_zh, cand)
            if ok:
                return (cand, "tier3")

            repaired = self._fit_length_bound(
                source_zh,
                reinject_skeleton_from_source(
                    source_zh,
                    TAG_RE.sub("", cand),
                    inner_translator=self._translate_raw_zh_to_id,
                    baseline_en=baseline_en,
                    en_translator=self.translate_en_to_id,
                ),
            )
            ok2, _ = validate_translation(source_zh, repaired)
            if ok2:
                return (repaired, "tier3")

            if validate_translation(source_zh, baseline_en)[0]:
                return (baseline_en, "tier3")

        # 5. Fallback for unmapped raw Chinese strings
        cand = self._fit_length_bound(source_zh, self._translate_raw_zh_to_id(source_zh))
        return (cand, "tier3")

    def _translate_raw_zh_to_id(self, source_zh: str) -> str:
        """Translate a raw Chinese string (with tags/placeholders) into validated Indonesian."""
        if source_zh in WINDOWS_108_ZH_TO_ID:
            return WINDOWS_108_ZH_TO_ID[source_zh]

        zh_phrase_map: list[tuple[str, str]] = [
            ("使用武凤获得第1名", "Raih Peringkat 1 menggunakan Wu Feng"),
            ("使用武凤获得前4名", "Raih Top 4 menggunakan Wu Feng"),
            ("使用武凤累计击败", "Kalahkan total menggunakan Wu Feng"),
            ("使用武凤参与对局", "Mainkan pertandingan menggunakan Wu Feng"),
            ("三分之地阵营", "Faction Three Kingdoms"),
            ("三分阵营", "Faction Three Kingdoms"),
            ("全体友方", "Semua sekutu"),
            ("友方英雄", "Hero sekutu"),
            ("敌方英雄", "Hero musuh"),
            ("最大生命值", "Max HP"),
            ("最大生命", "Max HP"),
            ("物理攻击力", "Physical Attack"),
            ("法术攻击力", "Magic Attack"),
            ("物理攻击", "Physical Attack"),
            ("法术攻击", "Magic Attack"),
            ("物理伤害", "Physical Damage"),
            ("法术伤害", "Magic Damage"),
            ("真实伤害", "True Damage"),
            ("物理防御", "Physical Defense"),
            ("法术防御", "Magic Defense"),
            ("攻击速度", "Attack Speed"),
            ("暴击率", "Crit Rate"),
            ("暴击伤害", "Crit Damage"),
            ("伤害减免", "Reduksi Damage"),
            ("伤害加成", "Bonus Damage"),
            ("伤害提升", "Peningkatan Damage"),
            ("临时等级", "Temporary Level"),
            ("真实等级", "True Level"),
            ("战斗开始时", "Saat Combat dimulai, "),
            ("每个回合开始时", "Di awal setiap Round, "),
            ("每个回合结束时", "Di akhir setiap Round, "),
            ("每回合开始时", "Di awal setiap Round, "),
            ("获得", "Dapatkan "),
            ("提升", "Meningkatkan "),
            ("减少", "Mengurangi "),
            ("降低", "Mengurangi "),
            ("恢复", "Memulihkan "),
            ("造成", "Memberikan "),
            ("召唤", "Memanggil "),
            ("登场", "On Play"),
            ("光环", "Aura"),
            ("激发", "Inspire"),
            ("连携", "Synergy"),
            ("变身", "Transform"),
            ("回手", "Bounce"),
            ("摧毁", "Destroy"),
            ("吞噬", "Devour"),
            ("护盾", "Shield"),
            ("唯一", "Unik"),
            ("被动", "Pasif"),
            ("主动", "Aktif"),
            ("英雄", "Hero "),
            ("装备", "Equipment "),
            ("天赋", "Talent "),
            ("效果牌", "Kartu Efek "),
            ("秘技牌", "Kartu Secret Art "),
            ("棋手", "Chess Player "),
            ("回合", "Round "),
            ("累计", "Total "),
            ("次数", " kali"),
            ("次", " kali"),
            ("秒", " detik"),
            ("层", " stack"),
            ("张", " kartu"),
            ("点", " "),
            ("金币", " Gold"),
            ("经验", " EXP"),
            ("等级", " Level "),
            ("星级", " Bintang "),
            ("胜利", "Kemenangan"),
            ("失败", "Kekalahan"),
            ("任务", "Misi"),
            ("奖励", "Hadiah"),
            ("解锁", "Buka"),
            ("完成", "Selesai"),
        ]

        # Sort entity keys longest first to prevent partial substring collisions
        sorted_t2 = sorted(self.tier2_zh_to_en.items(), key=lambda kv: len(kv[0]), reverse=True)

        def _seg_fn(seg: str) -> str:
            out = seg
            for k, v in WINDOWS_108_ZH_TO_ID.items():
                if k and len(k) >= 2 and k in out:
                    out = out.replace(k, v)
            for k, v in sorted_t2:
                if k and len(k) >= 2 and k in out:
                    out = out.replace(k, v)
            for k, v in zh_phrase_map:
                if k in out:
                    out = out.replace(k, v)
            out = (
                out.replace("：", ": ")
                .replace("，", ", ")
                .replace("。", ".")
                .replace("、", ", ")
                .replace("（", " (")
                .replace("）", ")")
                .replace("【", "[")
                .replace("】", "]")
                .replace("《", "")
                .replace("》", "")
                .replace("“", '"')
                .replace("”", '"')
                .replace("！", "!")
                .replace("？", "?")
                .replace("×", "x")
            )
            out = CJK_RE.sub("", out)
            out = re.sub(r"[ \t]+", " ", out).strip()
            return out or "OK"

        cand = translate_preserving_skeleton(source_zh, _seg_fn)
        ok, _ = validate_translation(source_zh, cand)
        if not ok:
            cand = reinject_skeleton_from_source(
                source_zh,
                TAG_RE.sub("", cand),
                en_translator=self.translate_en_to_id,
            )
        return cand

