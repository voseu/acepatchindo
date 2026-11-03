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
    const wchar_t* app_name;
    const wchar_t* app_title;
    const wchar_t* version_badge;
    const wchar_t* game_badge;
    const wchar_t* sub_header;

    // Navigation
    const wchar_t* nav_dashboard;
    const wchar_t* nav_patcher;
    const wchar_t* nav_android;
    const wchar_t* nav_settings;

    // Toolbar Actions
    const wchar_t* btn_install;
    const wchar_t* btn_restore;
    const wchar_t* btn_verify;
    const wchar_t* btn_browse;
    const wchar_t* btn_autodetect;
    const wchar_t* btn_clear;

    // Header Quick Toggles
    const wchar_t* toggle_ui_id;
    const wchar_t* toggle_ui_en;
    const wchar_t* toggle_mode_id;
    const wchar_t* toggle_mode_en;

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

    // Console Header & Hints
    const wchar_t* console_game_path_label;
    const wchar_t* console_placeholder;

    // Settings
    const wchar_t* settings_ui_lang_title;
    const wchar_t* settings_ui_lang_desc;
    const wchar_t* settings_patch_mode_title;
    const wchar_t* settings_patch_mode_desc;
    const wchar_t* settings_game_dir_title;
    const wchar_t* settings_game_dir_desc;

    // Android USB
    const wchar_t* android_title;
    const wchar_t* android_desc;
    const wchar_t* android_btn_scan;
    const wchar_t* android_btn_patch;
    const wchar_t* android_btn_recover;

    // Copyright / footer
    const wchar_t* copyright_label;
};

static const Strings STRINGS_ID = {
    L"Celeslib",
    L"Celeslib Honor of Kings: Ace Patcher",
    L"v1.0.0",
    L"Game Build 1.4.12",
    L"Eksekutor Patch & Lokalisasi Honor of Kings: Ace",

    L"Dashboard",
    L"Patcher",
    L"Android (USB)",
    L"Pengaturan",

    L"Pasang Patch",
    L"Pulihkan File",
    L"Periksa File",
    L"Pilih Folder",
    L"Auto-Detect",
    L"Bersihkan",

    L"UI: ID",
    L"UI: EN",
    L"Mode: ID Hybrid",
    L"Mode: EN Full",

    L"SIAP",
    L"MEMPROSES",
    L"TERPASANG",
    L"FILE ASLI",
    L"GALAT",

    L"Konfirmasi Pemasangan",
    L"Pasang patch Honor of Kings: Ace ke direktori game terpilih?",
    L"Konfirmasi Pemulihan",
    L"Pulihkan seluruh file asli game dari cadangan?",

    L"Jalur Game:",
    L"Belum ada aktivitas. Klik 'Pasang Patch' atau 'Periksa File' untuk memulai.",

    L"Bahasa Antarmuka (UI Language)",
    L"Pilih bahasa tampilan untuk menu dan antarmuka aplikasi patcher.",
    L"Mode Bahasa Patch Game (Game Patch Mode)",
    L"Pilih mode terjemahan: ID Hybrid (Bahasa Indonesia) atau EN Full (Bahasa Inggris 100%).",
    L"Direktori Game Honor of Kings: Ace",
    L"Jalur folder yang berisi berkas WXQ.exe dan WXQ_Data/Package/builtin.",

    L"Patcher Honor of Kings: Ace Android (USB)",
    L"Hubungkan perangkat Android dengan mode USB Debugging aktif untuk memasang patch.",
    L"Pindai Perangkat",
    L"Pasang ke Android",
    L"Pulihkan Android",

    L"© 2026 Celeslib • https://celeslib.my.id"
};

static const Strings STRINGS_EN = {
    L"Celeslib",
    L"Celeslib Honor of Kings: Ace Patcher",
    L"v1.0.0",
    L"Game Build 1.4.12",
    L"Honor of Kings: Ace Localization & Patch Executor",

    L"Dashboard",
    L"Patcher",
    L"Android (USB)",
    L"Settings",

    L"Install Patch",
    L"Restore Files",
    L"Check Files",
    L"Browse Folder",
    L"Auto-Detect",
    L"Clear Log",

    L"UI: ID",
    L"UI: EN",
    L"Mode: ID Hybrid",
    L"Mode: EN Full",

    L"READY",
    L"WORKING",
    L"INSTALLED",
    L"ORIGINALS",
    L"ERROR",

    L"Confirm Installation",
    L"Install the Honor of Kings: Ace patch to the selected game folder?",
    L"Confirm Restore",
    L"Restore original untouched game files from backup?",

    L"Game Path:",
    L"No recent activity. Click 'Install Patch' or 'Check Files' to begin.",

    L"User Interface Language",
    L"Select the display language for the patcher menus and application interface.",
    L"Game Patch Language Mode",
    L"Select patch translation mode: ID Hybrid (Indonesian gameplay) or EN Full (100% English).",
    L"Honor of Kings: Ace Game Directory",
    L"Path containing WXQ.exe and WXQ_Data/Package/builtin.",

    L"Honor of Kings: Ace Android Patcher (USB)",
    L"Connect an Android device with USB Debugging enabled to apply the patch.",
    L"Scan Device",
    L"Patch Android",
    L"Recover Android",

    L"© 2026 Celeslib • https://celeslib.my.id"
};

inline const Strings& GetStrings(UiLang lang) {
    return (lang == UiLang::EN) ? STRINGS_EN : STRINGS_ID;
}
