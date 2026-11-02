"""Windows Missing 108 Strings Split: 18 Gameplay Descriptions (ID) and 90 Non-Target Strings (EN)."""

from __future__ import annotations

# Exactly 18 target gameplay descriptions kept in Bahasa Indonesia
WINDOWS_108_TARGET_DESC_ID: dict[str, str] = {
    "转移后清除自身负面状态，并在5秒内免疫受到的控制。": (
        "Setelah berpindah, menghapus debuff diri sendiri dan kebal terhadap Crowd Control selama 5 detik."
    ),
    "转移后获得20%伤害加成。": "Setelah berpindah, dapatkan +20% Bonus Damage.",
    "战斗开始时，随机传送1个4-5阶临时等级为回合数×12的英雄进入战场（不含卡牌效果），并携带3件适配装备。": (
        "Saat Combat dimulai, pindahkan secara acak 1 Hero Tier 4-5 dengan Temporary Level sebesar "
        "(Round x12) ke medan tempur (tanpa efek kartu), membawa 3 Equipment yang sesuai."
    ),
    "若<color=#ffffff><b>枫叶舞</b></color>英雄被移除，其真实等级的25%会保留给下一个<color=#ffffff><b>枫叶舞</b></color>英雄，若为被出售，则保留75%真实等级，限一次。": (
        "Jika Hero <color=#ffffff><b>Maple Leaf Dance</b></color> dihapus, 25% True Level-nya diwariskan ke Hero "
        "<color=#ffffff><b>Maple Leaf Dance</b></color> berikutnya; jika dijual, mewariskan 75% True Level (maks 1 kali)."
    ),
    "若<color=#FFE897>枫叶舞</color>英雄被移除，其真实等级的25%会保留给下一个<color=#FFE897>枫叶舞</color>英雄，若为被出售，则保留75%真实等级，限一次。": (
        "Jika Hero <color=#FFE897>Maple Leaf Dance</color> dihapus, 25% True Level-nya diwariskan ke Hero "
        "<color=#FFE897>Maple Leaf Dance</color> berikutnya; jika dijual, mewariskan 75% True Level (maks 1 kali)."
    ),
    "获得1张装备牌<color=#FFE897>三分旗帜</color>：造成伤害的40%平摊治疗所有【三分】英雄（仅【三分】英雄可穿戴）。": (
        "Dapatkan 1 Kartu Equipment <color=#FFE897>Three Kingdoms Banner</color>: memulihkan HP semua Hero "
        "[Three Kingdoms] secara merata sebesar 40% dari Damage yang diberikan (hanya untuk Hero [Three Kingdoms])."
    ),
    "场上随机英雄等级+5，触发{DaQiao_TideTimes:3}次，若对象为<b>温柔呼唤</b>的英雄则额外等级+5，每次使用后，触发次数+2。": (
        "Hero acak di medan tempur mendapat Level +5, terpicu {DaQiao_TideTimes:3} kali; jika target adalah Hero "
        "<b>Gentle Call</b>, mendapat tambahan Level +5. Setiap digunakan, jumlah picuan +2."
    ),
    "枫叶舞指定的英雄击败3/5/9/15名敌方英雄，获得1张秘技牌<b>翩跹舞步</b>并为枫叶舞解锁1项特性（共4项）。": (
        "Hero yang ditunjuk Maple Leaf Dance mengalahkan 3/5/9/15 Hero musuh, dapatkan 1 Kartu Secret Art "
        "<b>Graceful Dance</b> dan buka 1 trait untuk Maple Leaf Dance (total 4 trait)."
    ),
    "枫叶舞指定的英雄累积击败3/5/9/15名敌方英雄后，阿离获得1张<color=#FFE897>翩跹舞步</color>，累计完成4次后任务需求固定为15。\n<color=#FFE897>翩跹舞步</color>：为<color=#FFE897>枫叶舞</color>挑选1张强化牌。": (
        "Setelah Hero yang ditunjuk Maple Leaf Dance mengalahkan total 3/5/9/15 Hero musuh, Arli mendapat 1 "
        "<color=#FFE897>Graceful Dance</color>; setelah selesai 4 kali, syarat misi tetap 15.\n"
        "<color=#FFE897>Graceful Dance</color>: Pilih 1 kartu penguat untuk <color=#FFE897>Maple Leaf Dance</color>."
    ),
    "每4个回合，乔汐获得1张<color=#FFE897>潮汐的交响</color>。\n<color=#FFE897>潮汐的交响</color>：场上随机5个英雄等级+4。": (
        "Setiap 4 Round, Qiao Xi mendapat 1 <color=#FFE897>Symphony of Tides</color>.\n"
        "<color=#FFE897>Symphony of Tides</color>: 5 Hero acak di medan tempur mendapat Level +4."
    ),
    "每4个回合，获得1张秘技牌<b>潮汐的交响</b>。": (
        "Setiap 4 Round, dapatkan 1 Kartu Secret Art <b>Symphony of Tides</b>."
    ),
    "每回合开始时，自动触发1次孙尚香【登场】词条效果。": (
        "Di awal setiap Round, otomatis memicu efek [On Play] Lady Sun 1 kali."
    ),
    "每回合开始时，触发1次<color=#FFE897>孙尚香</color>卡牌效果。": (
        "Di awal setiap Round, memicu efek kartu <color=#FFE897>Lady Sun</color> 1 kali."
    ),
    "立刻在<color=#FFE897>嬴政和武则天中随机一人</color>，下场战斗开始时使其吸收<color=#FFE897>其他友军</color>的等级和初始法力值。（使用后强化吸收能力）": (
        "Segera pilih acak 1 dari <color=#FFE897>Ying Zheng atau Wu Zetian</color>; saat Combat berikutnya dimulai, "
        "ia menyerap Level dan Mana awal <color=#FFE897>sekutu lainnya</color>. (Memperkuat daya serap setelah dipakai)"
    ),
    "<color=#ffffffbf>被动：</color>圣殿骑士冲锋时，对路径敌人造成<color=#dfa15e>[0]点物理伤害</color><color=#dfa15e>（[1]+[2]%自身最大生命值）</color>，随后戳刺敌人，造成<color=#dfa15e>[3]点物理伤害</color><color=#dfa15e>（[4]+[5]%自身最大生命值）</color>。\n<color=#ffffffbf>主动：</color>获得15%伤害加成，持续5秒。": (
        "<color=#ffffffbf>Pasif:</color> Saat Templar Knight menerjang, memberikan <color=#dfa15e>[0] Physical Damage</color>"
        "<color=#dfa15e> ([1]+[2]% Max HP diri)</color> ke musuh di jalur, lalu menusuk musuh sebesar "
        "<color=#dfa15e>[3] Physical Damage</color><color=#dfa15e> ([4]+[5]% Max HP diri)</color>.\n"
        "<color=#ffffffbf>Aktif:</color> Dapatkan +15% Bonus Damage selama 5 detik."
    ),
    "仆从伤害提升至100%法术攻击力，生命值恢复提升至100%法术攻击力": (
        "Damage Minion meningkat jadi 100% Magic Attack, pemulihan HP meningkat jadi 100% Magic Attack"
    ),
    "芈月为等级最高的近战友军召唤1只暗影仆从协助战斗，持续10秒。仆从每次攻击造成<color=#d487e4>80%芈月法术攻击力的法术伤害</color>并为友军恢复<color=#d487e4>80%芈月法术攻击力</color><color=#9ff5d0>的生命值</color>，同时窃取目标1点<color=#dfa15e>物理防御</color>和<color=#d487e4>法术防御</color>转移给友军（最多30层，持续至回合结束）。": (
        "Mi Yue memanggil 1 Shadow Servant bagi sekutu Melee berlevel tertinggi selama 10 detik. Setiap serangan Servant "
        "memberikan <color=#d487e4>Magic Damage sebesar 80% Magic Attack Mi Yue</color> dan memulihkan "
        "<color=#d487e4>80% Magic Attack Mi Yue</color><color=#9ff5d0> sebagai HP</color> ke sekutu, serta mencuri 1 "
        "<color=#dfa15e>Physical Defense</color> dan <color=#d487e4>Magic Defense</color> target untuk sekutu (maks 30 stack hingga akhir Round)."
    ),
    "选择棋手武凤，一起化万法为己用！通过棋手技能随机获得一张他人的秘技牌，每局都能打出意料之外的组合。": (
        "Pilih Chess Player Wu Feng dan kuasai segala jurus! Lewat Skill Chess Player, dapatkan acak 1 Kartu Secret Art "
        "milik lawan untuk menciptakan kombo tak terduga di setiap pertandingan."
    ),
}

# Exactly 90 non-target strings kept in clean English
WINDOWS_108_NONTARGET_EN: dict[str, str] = {
    "孙尚香·强化": "Lady Sun: Empowered",
    "<color=#ffffff><color=#ffffff><b>唯一</b></color></color>\n攻击速度+30%。攻速上限改为5.0。战斗期间，每获得2点法力值，提升1%攻击速度。": (
        "<color=#ffffff><color=#ffffff><b>Unique</b></color></color>\n"
        "Attack Speed +30%. Max Attack Speed increased to 5.0. During Combat, gain 1% Attack Speed for every 2 Mana gained."
    ),
    "仅三分英雄穿戴。将受到伤害的40%转化为治疗量，平摊给所有场上【三分】英雄。": (
        "Three Kingdoms Heroes only. Converts 40% of Damage taken into Healing, shared equally among all Three Kingdoms Heroes on the field."
    ),
    "仅三分英雄穿戴。将造成伤害的40%转化为治疗量，平摊给所有【三分】英雄。": (
        "Three Kingdoms Heroes only. Converts 40% of Damage dealt into Healing, shared equally among all Three Kingdoms Heroes."
    ),
    "传送{0}级": "Teleport Lv.{0}",
    "将造成伤害的40%转化为治疗量，平摊给所有【三分】英雄。": (
        "Converts 40% of Damage dealt into Healing, shared equally among all Three Kingdoms Heroes."
    ),
    "万象大赛每个英雄首次达100级可领取奖励": (
        "Claim rewards when each Hero reaches Lv.100 for the first time in the ACE Tournament"
    ),
    "图片缓存目录": "Image Cache Directory",
    "完成任务获取棋手武凤奖励": "Complete missions to obtain Chess Player Wu Feng rewards",
    "应援失败，请重新尝试": "Support failed, please try again",
    "您已经隐身2天啦，需要解除吗?": "You have been invisible for 2 days. Disable invisibility?",
    "竞猜总数": "Total Predictions",
    "钻石消耗": "Diamonds Spent",
    "<color=#98cbff>一、活动规则</color>\n<color=#FFFFFF>1、完成任务可领取武凤信物，足够的信物可兑换奖励。</color>\n<color=#FFFFFF>2、每日任务将于每天0点刷新，棋手任务仅可完成1次。</color>\n<color=#FFFFFF>3、若进行消极对局如挂机等行为，则无法完成对局任务哦。</color>": (
        "<color=#98cbff>I. Event Rules</color>\n"
        "<color=#FFFFFF>1. Complete missions to claim Wu Feng Tokens; exchange enough tokens for rewards.</color>\n"
        "<color=#FFFFFF>2. Daily missions refresh at 00:00 every day; Chess Player missions can only be completed once.</color>\n"
        "<color=#FFFFFF>3. Negative gameplay such as being AFK will prevent mission completion.</color>"
    ),
    "<color=#FFFFFFFF>[组队]{0}:</color>": "<color=#FFFFFFFF>[Team]{0}:</color>",
    "[系统]组队邀约": "[System] Team Invite",
    "【有分同享】组队邀请：万象大赛-排位": "[Share Points] Team Invite: ACE Tournament - Ranked",
    "万象大赛将棋手武凤升至6级": "Upgrade Chess Player Wu Feng to Lv.6 in the ACE Tournament",
    "万象大赛用棋手武凤获得前三名": "Reach Top 3 with Chess Player Wu Feng in the ACE Tournament",
    "万象大赛用棋手武凤获得第一名": "Reach 1st Place with Chess Player Wu Feng in the ACE Tournament",
    "万象王者{0}": "Vientiane King {0}",
    "下局是否继续和当前队友一起玩？": "Continue playing with your current teammates next match?",
    "下载管理": "Download Manager",
    "今日可上架价格范围：{0}-{1}": "Price range for listing today: {0}-{1}",
    "今日宜摸鱼7天限时卡": "7-Day Trial Card: Relax Today",
    "你去争第一吧，算我让你的。": "Go take 1st place, consider it my gift to you.",
    "使用棋手【乔汐】，在万象大赛中召唤1名临时等级为200级的英雄": (
        "Use Chess Player [Qiao Xi] and summon 1 Hero with Temporary Level 200 in the ACE Tournament"
    ),
    "公共": "Public",
    "再上<color=#ffffff>{0}</color>分可获得<color=#ffffff>{1}</color>": "Gain <color=#ffffff>{0}</color> more points to obtain <color=#ffffff>{1}</color>",
    "再上<color=#ffffff>{0}</color>分超过": "Gain <color=#ffffff>{0}</color> more points to surpass",
    "再盈利<color=#ffffff>{0}</color>可获得<color=#ffffff>{1}</color>": "Earn <color=#ffffff>{0}</color> more profit to obtain <color=#ffffff>{1}</color>",
    "再盈利<color=#ffffff>{0}</color>超过": "Earn <color=#ffffff>{0}</color> more profit to surpass",
    "可上架价格范围已更新，请稍后再试": "Listing price range updated, please try again later",
    "咱们同心协力，先把其他人送走。": "Let us work together and take out the others first.",
    "图片已保存至<color=#98CBFF>{0}</color>": "Image saved to <color=#98CBFF>{0}</color>",
    "在钻石狂潮、王牌对决和棋手竞猜玩法中，可使用本抵扣券减免1000钻石。（钻石狂潮每次限用1张）": (
        "In Diamond Frenzy, Ace Duel, and Chess Player Prediction modes, use this voucher for 1000 Diamonds off. (Max 1 per Diamond Frenzy)"
    ),
    "在钻石狂潮、王牌对决和棋手竞猜玩法中，可使用本抵扣券减免5000钻石。（钻石狂潮每次限用1张）": (
        "In Diamond Frenzy, Ace Duel, and Chess Player Prediction modes, use this voucher for 5000 Diamonds off. (Max 1 per Diamond Frenzy)"
    ),
    "在钻石狂潮、王牌对决和棋手竞猜玩法中，可使用本抵扣券减免500钻石。（钻石狂潮每次限用1张）": (
        "In Diamond Frenzy, Ace Duel, and Chess Player Prediction modes, use this voucher for 500 Diamonds off. (Max 1 per Diamond Frenzy)"
    ),
    "士别三日，技术暴涨这么多？": "After just three days apart, your skills improved this much?",
    "巅峰王者{0}": "Peak King {0}",
    "已使用抵扣券": "Voucher Used",
    "已放弃常规奖励": "Regular Rewards Forfeited",
    "已放弃常规奖励，获得特邀额外奖励": "Regular rewards forfeited; special invitation bonus rewards obtained",
    "当前无法购买积分保护卡": "Point Protection Card cannot be purchased at this time",
    "您已经隐身3天啦，好友都看不到你哦~需要解除吗?": "You have been invisible for 3 days and friends cannot see you~ Disable invisibility?",
    "您已隐身{0}天啦，好友们都在等你上线呢，需要解除吗?": "You have been invisible for {0} days and friends are waiting for you online. Disable invisibility?",
    "您已隐身{0}天啦，好友都很想念你哦，需要解除吗?": "You have been invisible for {0} days and friends really miss you. Disable invisibility?",
    "您正处于隐身状态哦，需要解除吗?": "You are currently invisible. Disable invisibility?",
    "感觉这把有高手啊？": "Feels like there are pro players in this match?",
    "我要开始表演了，好好看，好好学。": "I am about to put on a show. Watch closely and learn well.",
    "战力前列的棋手": "Top Combat Power Chess Players",
    "打开文件夹": "Open Folder",
    "打开礼包，必定获得爱心投放1天限时卡，并且随机获得以下奖励：\n夺宝币*2、香香·热情轰炸(30天)*1、常小娥·月之祈福(30天)*1、白歌·剑意纵横(30天)*1、趣味桌游*1、100%黑巧克力*1、小鹿玩偶*1、小动物捏捏*1、赢律（棋手）、渡梦传送特效。\n打开第50个礼包必定获得：渡梦传送特效！": (
        "Open the gift pack to receive Heart Drop 1-Day Trial Card, plus a random reward:\n"
        "Treasure Coins*2, Lady Sun: Fiery Barrage (30 Days)*1, Little Chang'e: Moon Blessing (30 Days)*1, "
        "Bai Ge: Sword Intent (30 Days)*1, Fun Board Game*1, 100% Dark Chocolate*1, Fawn Plush*1, Animal Squishy*1, "
        "Ying Lu (Chess Player), Dream Crossing Teleport Effect.\nOpening the 50th pack guarantees: Dream Crossing Teleport Effect!"
    ),
    "抵扣钻石": "Deduct Diamonds",
    "放弃翻牌将不会消耗每月翻牌次数，但也无法获得常规翻牌奖励（特邀额外奖励可正常获得）。确定放弃？": (
        "Skipping card flip will not consume monthly flip count, but regular flip rewards will not be obtained "
        "(special bonus rewards can still be obtained). Confirm skip?"
    ),
    "数据资源损坏！您需要重启游戏客户端进行资源修复。": "Data resource corrupted! Please restart the game client to repair resources.",
    "新闻": "News",
    "是否授权《王者万象棋》绑定您同平台的《王者荣耀》账号，获取账号信息以提供更好的游戏体验。\n授权内容：将《王者荣耀》好友关系与好友亲密度继承至《王者万象棋》。\n<color=#98CBFFFF>特别声明：亲密度仅首次授权时进行同步，后续不会再同步；继承的数值以本周一王者荣耀内亲密度数值为准（不同账号同步时间存在延迟）。</color>": (
        "Authorize Honor of Kings: Ace to link your Honor of Kings account on the same platform to improve gameplay experience?\n"
        "Authorization Content: Inherit Honor of Kings friends and Intimacy to Honor of Kings: Ace.\n"
        "<color=#98CBFFFF>Special Note: Intimacy only syncs upon first authorization and will not sync again later; "
        "inherited values are based on this Monday's values in Honor of Kings (sync time may vary between accounts).</color>"
    ),
    "更改目录": "Change Directory",
    "最强王者{0}": "Strongest King {0}",
    "朋友们，下局我们继续排啊~": "Friends, let us queue up together again next match~",
    "朋友们，打完这局我有点事儿，下局不一起排了~": "Friends, I have something to do after this match, cannot queue together next round~",
    "栏位扩充卡物品获取配置失败，请稍后再试": "Failed to load Slot Expansion Card item configuration, please try again later",
    "棋手武凤攻略": "Chess Player Wu Feng Guide",
    "武凤攻略": "Wu Feng Guide",
    "段位需达到倔强青铜方可发布招募！": "Must reach Stubborn Bronze rank to post recruitment!",
    "渡梦传送特效7天限时卡": "7-Day Trial Card: Dream Crossing Teleport Effect",
    "渡梦传送特效礼包": "Dream Crossing Teleport Effect Bundle",
    "玉环幻彩音阶7天限时卡": "7-Day Trial Card: Yu Huan Prismatic Scale",
    "玩家间亲密度值需高于{0}": "Intimacy between players must be higher than {0}",
    "由于您在刚刚的对局中选择了不继续游戏，返回时是否要退出队伍？": "Since you chose not to continue in the previous match, leave the team upon return?",
    "留在队内": "Stay in Team",
    "系统会按照最优方案自动扣除抵扣券": "The system will automatically apply vouchers according to the optimal plan",
    "自己人，下手轻点。": "We are on the same side, take it easy on me.",
    "获得棋盘【今日宜摸鱼】7天限时体验。": "Obtained 7-day trial of Chessboard [Relax Today].",
    "获得特效【渡梦传送特效】7天限时体验。": "Obtained 7-day trial of Effect [Dream Crossing].",
    "获得皮肤【玉环幻彩音阶】7天限时体验。": "Obtained 7-day trial of Skin [Yu Huan Prismatic Scale].",
    "该亲密度下的选手可在王者{0}分以内有分同享": "Players at this Intimacy level can Share Points within {0} King points",
    "该阵容已收藏至我的阵容": "Lineup saved to My Lineups",
    "请拖放下方已获取碎片到格内": "Please drag and drop the collected fragments below into the slot",
    "赛事": "Tournament",
    "超级周末：有分同享不限亲密度": "Super Weekend: Share Points with no Intimacy limit",
    "近期成交均价{0}，今日可上架价格范围：{1}-{2}": "Recent average transaction price {0}, price range for listing today: {1}-{2}",
    "这把我躺了，等你带飞。": "I am chilling this match, carry me to victory.",
    "这能输？我不服！": "How could we lose this? I contest this!",
    "退出队伍": "Leave Team",
    "通关棋手武凤训练关卡": "Complete Chess Player Wu Feng training stage",
    "道具数量不足，是否使用快捷购买？": "Insufficient items, use Quick Buy?",
    "部分购买成功": "Partial Purchase Successful",
    "钻石抵扣券": "Diamond Voucher",
}

WINDOWS_108_HYBRID_MAP: dict[str, str] = {
    **WINDOWS_108_NONTARGET_EN,
    **WINDOWS_108_TARGET_DESC_ID,
}

