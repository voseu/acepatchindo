#pragma once

#include <string>

enum class UiLang {
    ID = 0,
    EN = 1
};

enum class PatchMode {
    ID_HYBRID = 0,
    EN_FULL = 1
};

struct Strings {
    // Header (Zone 1)
    const wchar_t* app_name;
    const wchar_t* version_badge;
    const wchar_t* header_subtitle;

    // 3-Column Configuration Strip (Zone 2)
    const wchar_t* lbl_game_dir;
    const wchar_t* btn_autodetect;
    const wchar_t* btn_browse;

    const wchar_t* lbl_patch_mode;
    const wchar_t* seg_mode_id;
    const wchar_t* seg_mode_en;
    const wchar_t* desc_mode_id;
    const wchar_t* desc_mode_en;

    const wchar_t* lbl_ui_lang;
    const wchar_t* seg_ui_id;
    const wchar_t* seg_ui_en;
    const wchar_t* desc_ui;

    // Action Toolbar (Zone 3)
    const wchar_t* btn_install;
    const wchar_t* btn_restore;
    const wchar_t* btn_verify;
    const wchar_t* btn_android_scan;
    const wchar_t* btn_android_patch;
    const wchar_t* btn_android_recover;
    const wchar_t* btn_clear;

    // Diagnostic Console (Zone 4)
    const wchar_t* console_title;
    const wchar_t* console_placeholder;

    // Status Badges
    const wchar_t* status_ready;
    const wchar_t* status_working;
    const wchar_t* status_installed;
    const wchar_t* status_originals;
    const wchar_t* status_error;

    // Dialogs & Prompts
    const wchar_t* confirm_install_title;
    const wchar_t* confirm_install_msg;
    const wchar_t* confirm_restore_title;
    const wchar_t* confirm_restore_msg;

    // Bottom Bar (Zone 5)
    const wchar_t* bottom_engine_info;
    const wchar_t* bottom_copyright;
};

static const Strings STRINGS_ID = {
    L"Celeslib",
    L"v1.0.0",
    L"Honor of Kings: Ace Patcher • Game Build 1.4.12",

    L"DIREKTORI GAME (HOK: ACE)",
    L"Auto-Detect",
    L"Pilih Folder",

    L"MODE BAHASA PATCH",
    L"ID Hybrid",
    L"EN Full",
    L"UI Indonesia + Istilah MOBA English",
    L"100% Lokalisasi Bahasa Inggris",

    L"BAHASA UI",
    L"Indonesia",
    L"English",
    L"Engine: 508 Tabel • 72.186 Entri",

    L"Pasang Patch",
    L"Pulihkan",
    L"Periksa",
    L"Pindai USB",
    L"Patch APK",
    L"Pulihkan APK",
    L"Clear",

    L"output.log — Celeslib Dual-State VFS Engine",
    L"Sistem siap. Klik 'Pasang Patch' atau 'Periksa' untuk memulai verifikasi VFS.",

    L"SIAP",
    L"MEMPROSES",
    L"TERPASANG",
    L"FILE ASLI",
    L"GALAT",

    L"Konfirmasi Pemasangan",
    L"Pasang patch Honor of Kings: Ace ke direktori game terpilih?",
    L"Konfirmasi Pemulihan",
    L"Pulihkan seluruh berkas asli game dari cadangan?",

    L"Offline Dual-State VFS Engine • 508 Protobuf Tables • SHA-256 Verified",
    L"© 2026 Celeslib • HoK: Ace 1.4.12 • v1.0.0"
};

static const Strings STRINGS_EN = {
    L"Celeslib",
    L"v1.0.0",
    L"Honor of Kings: Ace Patcher • Game Build 1.4.12",

    L"GAME DIRECTORY (HOK: ACE)",
    L"Auto-Detect",
    L"Browse Folder",

    L"GAME PATCH MODE",
    L"ID Hybrid",
    L"EN Full",
    L"Indonesian UI + MOBA English Terms",
    L"100% Full English Localization",

    L"UI LANGUAGE",
    L"Indonesia",
    L"English",
    L"Engine: 508 Tables • 72,186 Entries",

    L"Install Patch",
    L"Restore",
    L"Check",
    L"Scan USB",
    L"Patch APK",
    L"Recover APK",
    L"Clear",

    L"output.log — Celeslib Dual-State VFS Engine",
    L"System ready. Click 'Install Patch' or 'Check' to begin VFS verification.",

    L"READY",
    L"WORKING",
    L"INSTALLED",
    L"ORIGINALS",
    L"ERROR",

    L"Confirm Installation",
    L"Install the Honor of Kings: Ace patch to the selected game folder?",
    L"Confirm Restore",
    L"Restore original untouched game files from backup?",

    L"Offline Dual-State VFS Engine • 508 Protobuf Tables • SHA-256 Verified",
    L"© 2026 Celeslib • HoK: Ace 1.4.12 • v1.0.0"
};

inline const Strings& GetStrings(UiLang lang) {
    return (lang == UiLang::EN) ? STRINGS_EN : STRINGS_ID;
}
