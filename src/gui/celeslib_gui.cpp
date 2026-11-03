#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif

#include <windows.h>
#include <windowsx.h>
#include <dwmapi.h>
#include <gdiplus.h>
#include <shlobj.h>
#include <shlwapi.h>
#include <wincrypt.h>

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include "celeslib_logo_rgba.h"
#include "celeslib_i18n.h"

#pragma comment(lib, "gdiplus.lib")
#pragma comment(lib, "dwmapi.lib")
#pragma comment(lib, "shlwapi.lib")
#pragma comment(lib, "comdlg32.lib")
#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "crypt32.lib")

// Color Palette - Celeslib Ultra-Dark Carbon
namespace Theme {
    static const Gdiplus::Color BgCanvas(0xFF, 0x09, 0x09, 0x0B);       // #09090B
    static const Gdiplus::Color BgHeader(0xFF, 0x0B, 0x0B, 0x0E);       // #0B0B0E
    static const Gdiplus::Color BgSidebar(0xFF, 0x0D, 0x0D, 0x11);      // #0D0D11
    static const Gdiplus::Color BgPill(0xFF, 0x14, 0x14, 0x1A);         // #14141A
    static const Gdiplus::Color BgPillHover(0xFF, 0x1E, 0x1E, 0x28);    // #1E1E28
    static const Gdiplus::Color BgPillActive(0xFF, 0x2A, 0x20, 0x48);   // #2A2048
    static const Gdiplus::Color BorderDark(0xFF, 0x24, 0x24, 0x2E);     // #24242E
    static const Gdiplus::Color BorderHover(0xFF, 0x3E, 0x38, 0x56);    // #3E3856
    static const Gdiplus::Color AccentViolet(0xFF, 0x8B, 0x5C, 0xF6);   // #8B5CF6 Celeslib
    static const Gdiplus::Color AccentLight(0xFF, 0xA7, 0x8B, 0xFA);    // #A78BFA
    static const Gdiplus::Color AccentEmerald(0xFF, 0x10, 0xB9, 0x81);  // #10B981 Status OK
    static const Gdiplus::Color AccentRed(0xFF, 0xEF, 0x44, 0x44);      // #EF4444 Error
    static const Gdiplus::Color TextPrimary(0xFF, 0xF4, 0xF4, 0xF5);    // #F4F4F5
    static const Gdiplus::Color TextSecondary(0xFF, 0xA1, 0xA1, 0xAA);  // #A1A1AA
    static const Gdiplus::Color TextMuted(0xFF, 0x52, 0x52, 0x5B);      // #52525B
    static const Gdiplus::Color ConsoleBg(0xFF, 0x10, 0x10, 0x15);      // #101015
    static const Gdiplus::Color ConsoleGutter(0xFF, 0x0C, 0x0C, 0x10);  // #0C0C10
    static const Gdiplus::Color ConsoleMinimap(0xFF, 0x08, 0x08, 0x0C); // #08080C
}

enum class NavView {
    Dashboard = 0,
    Patcher = 1,
    Android = 2,
    Settings = 3
};

struct AppState {
    UiLang ui_lang = UiLang::ID;
    PatchMode patch_mode = PatchMode::ID_HYBRID;
    NavView current_view = NavView::Patcher;
    std::wstring game_dir;
    std::vector<std::wstring> log_lines;
    std::wstring status_text = L"SIAP";
    Gdiplus::Color status_color = Theme::AccentEmerald;
    bool is_busy = false;
    bool sidebar_collapsed = false;
    int hovered_btn = -1;
    std::mutex mtx;

    // Window dimensions
    int width = 980;
    int height = 620;
};

static AppState g_state;
static HWND g_hwnd = nullptr;

// Embedded Worker Protocol
static const char WORKER_MAGIC_HEADER[] = "CELESLIB_WORKER_V1";
static const size_t WORKER_EXACT_SIZE = 53927862;

// Static branding metadata signatures for PE inspection
volatile const char g_celeslib_signature[] =
    "Celeslib v1.0.0 (Game Build 1.4.12) - Pasang Patch / Install Patch - CELESLIB_UI_LANG - CELESLIB_PATCH_LANG";

// Utility: AppData directory
std::wstring GetCeleslibAppDataDir() {
    wchar_t path[MAX_PATH];
    if (SUCCEEDED(SHGetFolderPathW(NULL, CSIDL_LOCAL_APPDATA, NULL, 0, path))) {
        std::wstring p = std::wstring(path) + L"\\Celeslib\\HoK Ace Patcher";
        CreateDirectoryW((std::wstring(path) + L"\\Celeslib").c_str(), NULL);
        CreateDirectoryW(p.c_str(), NULL);
        return p;
    }
    return L".";
}

// Config load & save
void LoadConfig() {
    std::wstring cfg_path = GetCeleslibAppDataDir() + L"\\config.json";
    std::ifstream f(cfg_path.c_str());
    if (!f.is_open()) return;
    std::string line;
    while (std::getline(f, line)) {
        if (line.find("\"ui_lang\": \"en\"") != std::string::npos) {
            g_state.ui_lang = UiLang::EN;
        } else if (line.find("\"ui_lang\": \"id\"") != std::string::npos) {
            g_state.ui_lang = UiLang::ID;
        }
        if (line.find("\"patch_mode\": \"en\"") != std::string::npos) {
            g_state.patch_mode = PatchMode::EN_FULL;
        } else if (line.find("\"patch_mode\": \"id\"") != std::string::npos) {
            g_state.patch_mode = PatchMode::ID_HYBRID;
        }
        if (line.find("\"sidebar_collapsed\": true") != std::string::npos) {
            g_state.sidebar_collapsed = true;
        }
    }
}

void SaveConfig() {
    std::wstring cfg_path = GetCeleslibAppDataDir() + L"\\config.json";
    std::ofstream f(cfg_path.c_str());
    if (!f.is_open()) return;
    f << "{\n";
    f << "  \"ui_lang\": \"" << (g_state.ui_lang == UiLang::EN ? "en" : "id") << "\",\n";
    f << "  \"patch_mode\": \"" << (g_state.patch_mode == PatchMode::EN_FULL ? "en" : "id") << "\",\n";
    f << "  \"sidebar_collapsed\": " << (g_state.sidebar_collapsed ? "true" : "false") << "\n";
    f << "}\n";
}

// Add Console Log
void AppendLog(const std::wstring& msg) {
    std::lock_guard<std::mutex> lock(g_state.mtx);
    g_state.log_lines.push_back(msg);
    if (g_hwnd) {
        InvalidateRect(g_hwnd, NULL, FALSE);
    }
}

// Helper: Convert string between UTF-8 and Wide
std::wstring Utf8ToWide(const std::string& str) {
    if (str.empty()) return std::wstring();
    int len = MultiByteToWideChar(CP_UTF8, 0, str.c_str(), (int)str.size(), NULL, 0);
    if (len <= 0) return std::wstring();
    std::wstring wstr(len, 0);
    MultiByteToWideChar(CP_UTF8, 0, str.c_str(), (int)str.size(), &wstr[0], len);
    return wstr;
}

// Parser for result.json generated by ace-worker.exe
struct WorkerResult {
    std::wstring state;
    std::wstring message;
    std::wstring game_dir;
    bool restore_available = false;
};

WorkerResult ParseWorkerResult(const std::wstring& json_file_path) {
    WorkerResult res;
    std::ifstream f(json_file_path.c_str(), std::ios::binary);
    if (!f.is_open()) return res;

    std::stringstream ss;
    ss << f.rdbuf();
    std::string json = ss.str();

    auto extract_string_field = [&](const std::string& key) -> std::string {
        std::string pattern = "\"" + key + "\"";
        size_t p = json.find(pattern);
        if (p == std::string::npos) return "";
        p = json.find(':', p);
        if (p == std::string::npos) return "";
        p = json.find('"', p);
        if (p == std::string::npos) return "";
        size_t start = p + 1;
        size_t end = start;
        while (end < json.size()) {
            if (json[end] == '"' && json[end - 1] != '\\') break;
            end++;
        }
        if (end > json.size()) return "";
        std::string raw = json.substr(start, end - start);
        std::string unescaped;
        for (size_t i = 0; i < raw.size(); ++i) {
            if (raw[i] == '\\' && i + 1 < raw.size()) {
                if (raw[i + 1] == '"') { unescaped += '"'; i++; }
                else if (raw[i + 1] == '\\') { unescaped += '\\'; i++; }
                else if (raw[i + 1] == 'n') { unescaped += '\n'; i++; }
                else if (raw[i + 1] == 'r') { unescaped += '\r'; i++; }
                else if (raw[i + 1] == 't') { unescaped += '\t'; i++; }
                else unescaped += raw[i];
            } else {
                unescaped += raw[i];
            }
        }
        return unescaped;
    };

    res.state = Utf8ToWide(extract_string_field("state"));
    res.message = Utf8ToWide(extract_string_field("message"));
    res.game_dir = Utf8ToWide(extract_string_field("game_dir"));

    size_t ra = json.find("\"restore_available\"");
    if (ra != std::string::npos) {
        size_t colon = json.find(':', ra);
        if (colon != std::string::npos) {
            std::string sub = json.substr(colon, 15);
            if (sub.find("true") != std::string::npos) {
                res.restore_available = true;
            }
        }
    }
    return res;
}

// Locate and extract embedded ace-worker.exe with 64-bit seeking and Windows CryptoAPI verification
bool LocateAndExtractWorker(std::wstring& out_worker_path) {
    wchar_t exe_path[MAX_PATH];
    GetModuleFileNameW(NULL, exe_path, MAX_PATH);

    HANDLE hFile = CreateFileW(exe_path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hFile == INVALID_HANDLE_VALUE) return false;

    LARGE_INTEGER liSize;
    if (!GetFileSizeEx(hFile, &liSize)) {
        CloseHandle(hFile);
        return false;
    }
    uint64_t file_size = (uint64_t)liSize.QuadPart;

    DWORD bytes_read = 0;

    // Check footer pointer (last 8 bytes)
    uint64_t sha_offset = 0;
    if (file_size > 74 + WORKER_EXACT_SIZE) {
        LARGE_INTEGER li;
        li.QuadPart = (LONGLONG)(file_size - 8);
        SetFilePointerEx(hFile, li, NULL, FILE_BEGIN);
        ReadFile(hFile, &sha_offset, 8, &bytes_read, NULL);
    }

    std::string sha256_hex;
    uint64_t worker_start = 0;

    if (sha_offset > 0 && sha_offset + 80 + WORKER_EXACT_SIZE <= file_size) {
        // Read SHA-256 header
        LARGE_INTEGER li;
        li.QuadPart = (LONGLONG)sha_offset;
        SetFilePointerEx(hFile, li, NULL, FILE_BEGIN);
        std::vector<char> hdr(80, 0);
        ReadFile(hFile, hdr.data(), 80, &bytes_read, NULL);
        std::string hdr_str(hdr.data(), bytes_read);
        if (hdr_str.find("ace-worker.exe") != std::string::npos) {
            sha256_hex = hdr_str.substr(0, 64);
            size_t name_pos = hdr_str.find("ace-worker.exe");
            worker_start = sha_offset + name_pos + 14;
        }
    }

    // Fallback: Fixed offsets (0x4CABFA, 0x4CAC4A)
    if (sha256_hex.empty() && file_size >= 0x3838C00) {
        LARGE_INTEGER li;
        li.QuadPart = 0x4CABFA;
        SetFilePointerEx(hFile, li, NULL, FILE_BEGIN);
        std::vector<char> hdr(80, 0);
        ReadFile(hFile, hdr.data(), 80, &bytes_read, NULL);
        std::string hdr_str(hdr.data(), bytes_read);
        if (hdr_str.find("ace-worker.exe") != std::string::npos) {
            sha256_hex = hdr_str.substr(0, 64);
            worker_start = 0x4CAC4A;
        }
    }

    if (sha256_hex.empty() || worker_start == 0) {
        CloseHandle(hFile);
        return false;
    }

    std::wstring app_data = GetCeleslibAppDataDir();
    std::wstring engine_dir = app_data + L"\\engine\\" + std::wstring(sha256_hex.begin(), sha256_hex.end());
    CreateDirectoryW((app_data + L"\\engine").c_str(), NULL);
    CreateDirectoryW(engine_dir.c_str(), NULL);

    out_worker_path = engine_dir + L"\\ace-worker.exe";

    // If already extracted, verify its exact size matches WORKER_EXACT_SIZE
    if (PathFileExistsW(out_worker_path.c_str())) {
        HANDLE hCheck = CreateFileW(out_worker_path.c_str(), GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
        if (hCheck != INVALID_HANDLE_VALUE) {
            LARGE_INTEGER sz;
            if (GetFileSizeEx(hCheck, &sz) && sz.QuadPart == (LONGLONG)WORKER_EXACT_SIZE) {
                CloseHandle(hCheck);
                CloseHandle(hFile);
                return true;
            }
            CloseHandle(hCheck);
            DeleteFileW(out_worker_path.c_str());
        }
    }

    // Extract worker payload with CryptoAPI SHA-256 verification
    LARGE_INTEGER liWorker;
    liWorker.QuadPart = (LONGLONG)worker_start;
    SetFilePointerEx(hFile, liWorker, NULL, FILE_BEGIN);

    HCRYPTPROV hProv = 0;
    HCRYPTHASH hHash = 0;
    if (!CryptAcquireContextW(&hProv, NULL, NULL, PROV_RSA_AES, CRYPT_VERIFYCONTEXT)) {
        CloseHandle(hFile);
        return false;
    }
    if (!CryptCreateHash(hProv, CALG_SHA_256, 0, 0, &hHash)) {
        CryptReleaseContext(hProv, 0);
        CloseHandle(hFile);
        return false;
    }

    HANDLE hOut = CreateFileW(out_worker_path.c_str(), GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hOut == INVALID_HANDLE_VALUE) {
        CryptDestroyHash(hHash);
        CryptReleaseContext(hProv, 0);
        CloseHandle(hFile);
        return false;
    }

    const DWORD CHUNK = 65536;
    std::vector<uint8_t> chunk(CHUNK);
    uint64_t remaining = WORKER_EXACT_SIZE;
    bool write_ok = true;

    while (remaining > 0) {
        DWORD to_read = (DWORD)std::min((uint64_t)CHUNK, remaining);
        if (!ReadFile(hFile, chunk.data(), to_read, &bytes_read, NULL) || bytes_read == 0) {
            write_ok = false;
            break;
        }
        CryptHashData(hHash, chunk.data(), bytes_read, 0);
        DWORD written = 0;
        if (!WriteFile(hOut, chunk.data(), bytes_read, &written, NULL) || written != bytes_read) {
            write_ok = false;
            break;
        }
        remaining -= bytes_read;
    }

    CloseHandle(hOut);

    bool hash_verified = false;
    if (write_ok && remaining == 0) {
        BYTE hashVal[32];
        DWORD hashLen = sizeof(hashVal);
        if (CryptGetHashParam(hHash, HP_HASHVAL, hashVal, &hashLen, 0)) {
            char actual_hex[65];
            for (int i = 0; i < 32; ++i) {
                sprintf_s(actual_hex + i * 2, 3, "%02X", hashVal[i]);
            }
            actual_hex[64] = '\0';
            if (_stricmp(actual_hex, sha256_hex.c_str()) == 0) {
                hash_verified = true;
            }
        }
    }

    CryptDestroyHash(hHash);
    CryptReleaseContext(hProv, 0);
    CloseHandle(hFile);

    if (!hash_verified) {
        DeleteFileW(out_worker_path.c_str());
        return false;
    }

    return true;
}

// Synchronously run worker process with stdout pipe streaming
int RunWorkerProcessSync(const std::wstring& cmd_str, std::wstring& out_stdout) {
    SECURITY_ATTRIBUTES sa = { sizeof(sa), NULL, TRUE };
    HANDLE hRead, hWrite;
    if (!CreatePipe(&hRead, &hWrite, &sa, 0)) return -1;
    SetHandleInformation(hRead, HANDLE_FLAG_INHERIT, 0);

    STARTUPINFOW si = { sizeof(si) };
    si.dwFlags |= STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
    si.hStdOutput = hWrite;
    si.hStdError = hWrite;
    si.wShowWindow = SW_HIDE;

    PROCESS_INFORMATION pi = { 0 };
    std::vector<wchar_t> cmd_buf(cmd_str.begin(), cmd_str.end());
    cmd_buf.push_back(0);

    if (!CreateProcessW(NULL, cmd_buf.data(), NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {
        CloseHandle(hWrite);
        CloseHandle(hRead);
        return -1;
    }

    CloseHandle(hWrite);

    char buf[512];
    DWORD read_bytes = 0;
    std::string accum;
    while (ReadFile(hRead, buf, sizeof(buf) - 1, &read_bytes, NULL) && read_bytes > 0) {
        buf[read_bytes] = 0;
        accum += buf;
    }

    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD exit_code = 0;
    GetExitCodeProcess(pi.hProcess, &exit_code);

    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    CloseHandle(hRead);

    out_stdout = Utf8ToWide(accum);
    return (int)exit_code;
}

// Asynchronously execute worker action with exact adaptive CLI protocol and result.json parsing
void ExecuteWorkerAction(const std::wstring& action, const std::wstring& game_path) {
    if (g_state.is_busy) return;
    g_state.is_busy = true;
    g_state.status_text = (g_state.ui_lang == UiLang::EN) ? L"WORKING" : L"MEMPROSES";
    g_state.status_color = Theme::AccentViolet;
    if (g_hwnd) InvalidateRect(g_hwnd, NULL, FALSE);

    std::thread([action, game_path]() {
        std::wstring worker_path;
        if (!LocateAndExtractWorker(worker_path)) {
            AppendLog(L"[ERROR] Gagal mengekstrak worker engine!");
            g_state.is_busy = false;
            g_state.status_text = (g_state.ui_lang == UiLang::EN) ? L"ERROR" : L"GALAT";
            g_state.status_color = Theme::AccentRed;
            if (g_hwnd) InvalidateRect(g_hwnd, NULL, FALSE);
            return;
        }

        std::wstring app_data = GetCeleslibAppDataDir();
        std::wstring work_dir = app_data + L"\\work";
        CreateDirectoryW(work_dir.c_str(), NULL);
        std::wstring result_path = work_dir + L"\\result.json";
        DeleteFileW(result_path.c_str());

        // Set environmental language triggers
        SetEnvironmentVariableW(L"CELESLIB_UI_LANG", g_state.ui_lang == UiLang::EN ? L"en" : L"id");
        SetEnvironmentVariableW(L"CELESLIB_PATCH_LANG", g_state.patch_mode == PatchMode::EN_FULL ? L"en" : L"id");

        std::wstringstream cmd;
        cmd << L"\"" << worker_path << L"\" " << action
            << L" --work \"" << work_dir << L"\""
            << L" --result \"" << result_path << L"\"";
        if (!game_path.empty() && action != L"discover") {
            cmd << L" --game-dir \"" << game_path << L"\"";
        }

        AppendLog(L"[INFO] Menjalankan: " + cmd.str());

        SECURITY_ATTRIBUTES sa = { sizeof(sa), NULL, TRUE };
        HANDLE hRead, hWrite;
        CreatePipe(&hRead, &hWrite, &sa, 0);
        SetHandleInformation(hRead, HANDLE_FLAG_INHERIT, 0);

        STARTUPINFOW si = { sizeof(si) };
        si.dwFlags |= STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
        si.hStdOutput = hWrite;
        si.hStdError = hWrite;
        si.wShowWindow = SW_HIDE;

        PROCESS_INFORMATION pi = { 0 };
        std::vector<wchar_t> cmd_buf(cmd.str().begin(), cmd.str().end());
        cmd_buf.push_back(0);

        if (CreateProcessW(NULL, cmd_buf.data(), NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {
            CloseHandle(hWrite);

            char buf[512];
            DWORD read_bytes = 0;
            std::string line_accum;
            while (ReadFile(hRead, buf, sizeof(buf) - 1, &read_bytes, NULL) && read_bytes > 0) {
                buf[read_bytes] = 0;
                line_accum += buf;
                size_t nl;
                while ((nl = line_accum.find('\n')) != std::string::npos) {
                    std::string single_line = line_accum.substr(0, nl);
                    if (!single_line.empty() && single_line.back() == '\r') single_line.pop_back();
                    line_accum.erase(0, nl + 1);
                    if (!single_line.empty()) {
                        AppendLog(Utf8ToWide(single_line));
                    }
                }
            }
            if (!line_accum.empty()) {
                AppendLog(Utf8ToWide(line_accum));
            }

            WaitForSingleObject(pi.hProcess, INFINITE);
            DWORD exit_code = 0;
            GetExitCodeProcess(pi.hProcess, &exit_code);
            CloseHandle(pi.hProcess);
            CloseHandle(pi.hThread);
            CloseHandle(hRead);

            // Read and parse result.json
            WorkerResult res = ParseWorkerResult(result_path);
            if (!res.message.empty()) {
                if (exit_code == 0) {
                    AppendLog(L"[OK] " + res.message);
                } else {
                    AppendLog(L"[ERROR] " + res.message);
                }
            }

            // Auto-update game_dir if discovered
            if (!res.game_dir.empty()) {
                g_state.game_dir = res.game_dir;
                AppendLog(L"[INFO] Direktori game terdeteksi: " + res.game_dir);
            }

            const Strings& s = GetStrings(g_state.ui_lang);
            if (exit_code == 0) {
                if (action == L"restore" || res.state == L"clean") {
                    g_state.status_text = s.status_originals;
                    g_state.status_color = Theme::AccentEmerald;
                } else if (action == L"install" || res.state == L"installed") {
                    g_state.status_text = s.status_installed;
                    g_state.status_color = Theme::AccentEmerald;
                } else {
                    g_state.status_text = s.status_ready;
                    g_state.status_color = Theme::AccentEmerald;
                }
                AppendLog(L"[OK] Operasi selesai dengan sukses.");
            } else {
                g_state.status_text = s.status_error;
                g_state.status_color = Theme::AccentRed;
                AppendLog(L"[ERROR] Operasi worker berakhir dengan kode: " + std::to_wstring(exit_code));
            }
        } else {
            CloseHandle(hWrite);
            CloseHandle(hRead);
            AppendLog(L"[ERROR] Gagal meluncurkan proses worker!");
            g_state.status_text = (g_state.ui_lang == UiLang::EN) ? L"ERROR" : L"GALAT";
            g_state.status_color = Theme::AccentRed;
        }

        g_state.is_busy = false;
        if (g_hwnd) InvalidateRect(g_hwnd, NULL, FALSE);
    }).detach();
}

// Asynchronously execute Android (USB) mobile-worker or mobile-recover action
void ExecuteMobileWorkerAction(const std::wstring& operation) {
    if (g_state.is_busy) return;
    g_state.is_busy = true;
    g_state.status_text = (g_state.ui_lang == UiLang::EN) ? L"WORKING" : L"MEMPROSES";
    g_state.status_color = Theme::AccentViolet;
    if (g_hwnd) InvalidateRect(g_hwnd, NULL, FALSE);

    std::thread([operation]() {
        std::wstring worker_path;
        if (!LocateAndExtractWorker(worker_path)) {
            AppendLog(L"[ERROR] Gagal mengekstrak worker engine!");
            g_state.is_busy = false;
            g_state.status_text = (g_state.ui_lang == UiLang::EN) ? L"ERROR" : L"GALAT";
            g_state.status_color = Theme::AccentRed;
            if (g_hwnd) InvalidateRect(g_hwnd, NULL, FALSE);
            return;
        }

        std::wstring app_data = GetCeleslibAppDataDir();
        std::wstring work_dir = app_data + L"\\work";
        CreateDirectoryW(work_dir.c_str(), NULL);

        SetEnvironmentVariableW(L"CELESLIB_UI_LANG", g_state.ui_lang == UiLang::EN ? L"en" : L"id");
        SetEnvironmentVariableW(L"CELESLIB_PATCH_LANG", g_state.patch_mode == PatchMode::EN_FULL ? L"en" : L"id");

        std::wstringstream cmd;
        if (operation == L"recover") {
            cmd << L"\"" << worker_path << L"\" mobile-recover --work \"" << work_dir << L"\"";
        } else {
            cmd << L"\"" << worker_path << L"\" mobile-worker --work \"" << work_dir << L"\" --operation " << operation;
        }

        AppendLog(L"[INFO] Menjalankan Android USB: " + cmd.str());

        SECURITY_ATTRIBUTES sa = { sizeof(sa), NULL, TRUE };
        HANDLE hRead, hWrite;
        CreatePipe(&hRead, &hWrite, &sa, 0);
        SetHandleInformation(hRead, HANDLE_FLAG_INHERIT, 0);

        STARTUPINFOW si = { sizeof(si) };
        si.dwFlags |= STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
        si.hStdOutput = hWrite;
        si.hStdError = hWrite;
        si.wShowWindow = SW_HIDE;

        PROCESS_INFORMATION pi = { 0 };
        std::vector<wchar_t> cmd_buf(cmd.str().begin(), cmd.str().end());
        cmd_buf.push_back(0);

        if (CreateProcessW(NULL, cmd_buf.data(), NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {
            CloseHandle(hWrite);

            char buf[512];
            DWORD read_bytes = 0;
            std::string line_accum;
            while (ReadFile(hRead, buf, sizeof(buf) - 1, &read_bytes, NULL) && read_bytes > 0) {
                buf[read_bytes] = 0;
                line_accum += buf;
                size_t nl;
                while ((nl = line_accum.find('\n')) != std::string::npos) {
                    std::string single_line = line_accum.substr(0, nl);
                    if (!single_line.empty() && single_line.back() == '\r') single_line.pop_back();
                    line_accum.erase(0, nl + 1);
                    if (!single_line.empty()) {
                        AppendLog(Utf8ToWide(single_line));
                    }
                }
            }
            if (!line_accum.empty()) {
                AppendLog(Utf8ToWide(line_accum));
            }

            WaitForSingleObject(pi.hProcess, INFINITE);
            DWORD exit_code = 0;
            GetExitCodeProcess(pi.hProcess, &exit_code);
            CloseHandle(pi.hProcess);
            CloseHandle(pi.hThread);
            CloseHandle(hRead);

            const Strings& s = GetStrings(g_state.ui_lang);
            if (exit_code == 0) {
                g_state.status_text = s.status_ready;
                g_state.status_color = Theme::AccentEmerald;
                AppendLog(L"[OK] Operasi Android USB selesai.");
            } else {
                g_state.status_text = s.status_error;
                g_state.status_color = Theme::AccentRed;
                AppendLog(L"[ERROR] Android USB berakhir dengan kode: " + std::to_wstring(exit_code));
            }
        } else {
            CloseHandle(hWrite);
            CloseHandle(hRead);
            AppendLog(L"[ERROR] Gagal meluncurkan proses mobile-worker!");
            g_state.status_text = (g_state.ui_lang == UiLang::EN) ? L"ERROR" : L"GALAT";
            g_state.status_color = Theme::AccentRed;
        }

        g_state.is_busy = false;
        if (g_hwnd) InvalidateRect(g_hwnd, NULL, FALSE);
    }).detach();
}

// Drawing Utilities
void FillRoundRect(Gdiplus::Graphics& g, const Gdiplus::Brush& brush, float x, float y, float w, float h, float r) {
    Gdiplus::GraphicsPath path;
    path.AddArc(x, y, r * 2, r * 2, 180, 90);
    path.AddArc(x + w - r * 2, y, r * 2, r * 2, 270, 90);
    path.AddArc(x + w - r * 2, y + h - r * 2, r * 2, r * 2, 0, 90);
    path.AddArc(x, y + h - r * 2, r * 2, r * 2, 90, 90);
    path.CloseFigure();
    g.FillPath(&brush, &path);
}

void DrawRoundRect(Gdiplus::Graphics& g, const Gdiplus::Pen& pen, float x, float y, float w, float h, float r) {
    Gdiplus::GraphicsPath path;
    path.AddArc(x, y, r * 2, r * 2, 180, 90);
    path.AddArc(x + w - r * 2, y, r * 2, r * 2, 270, 90);
    path.AddArc(x + w - r * 2, y + h - r * 2, r * 2, r * 2, 0, 90);
    path.AddArc(x, y + h - r * 2, r * 2, r * 2, 90, 90);
    path.CloseFigure();
    g.DrawPath(&pen, &path);
}

// Draw line-numbered monospace console with minimap
void RenderConsolePanel(Gdiplus::Graphics& g, int x, int y, int w, int h, const AppState& state,
                        Gdiplus::Font* fontMono, Gdiplus::Brush* textMutedBrush,
                        Gdiplus::Brush* textPrimaryBrush, Gdiplus::Brush* accentLightBrush,
                        Gdiplus::Brush* accentBrush, Gdiplus::Brush* textSecBrush) {
    using namespace Gdiplus;
    Pen borderPen(Theme::BorderDark, 1.0f);
    int gutter_w = 42;
    int minimap_w = 54;

    SolidBrush conBg(Theme::ConsoleBg);
    FillRoundRect(g, conBg, (float)x, (float)y, (float)w, (float)h, 6);
    DrawRoundRect(g, borderPen, (float)x, (float)y, (float)w, (float)h, 6);

    // Line number gutter
    SolidBrush gutterBg(Theme::ConsoleGutter);
    g.FillRectangle(&gutterBg, x, y, gutter_w, h);
    g.DrawLine(&borderPen, x + gutter_w, y, x + gutter_w, y + h);

    // Minimap strip
    SolidBrush minimapBg(Theme::ConsoleMinimap);
    g.FillRectangle(&minimapBg, x + w - minimap_w, y, minimap_w, h);
    g.DrawLine(&borderPen, x + w - minimap_w, y, x + w - minimap_w, y + h);

    const Strings& s = GetStrings(state.ui_lang);
    if (state.log_lines.empty()) {
        g.DrawString(L"001", -1, fontMono, PointF((float)x + 8, (float)y + 8), textMutedBrush);
        g.DrawString(s.console_placeholder, -1, fontMono, PointF((float)x + gutter_w + 12, (float)y + 8), textMutedBrush);
    } else {
        int line_y = y + 8;
        int max_visible = (h - 16) / 18;
        int start_idx = (int)state.log_lines.size() > max_visible ? (int)state.log_lines.size() - max_visible : 0;
        for (size_t i = start_idx; i < state.log_lines.size(); ++i) {
            wchar_t num_str[16];
            swprintf_s(num_str, L"%03d", (int)i + 1);
            g.DrawString(num_str, -1, fontMono, PointF((float)x + 8, (float)line_y), textMutedBrush);

            const std::wstring& line = state.log_lines[i];
            Brush* lineBrush = textPrimaryBrush;
            if (line.find(L"[OK]") != std::wstring::npos) lineBrush = accentLightBrush;
            else if (line.find(L"[ERROR]") != std::wstring::npos) lineBrush = accentBrush;
            else if (line.find(L"[INFO]") != std::wstring::npos) lineBrush = textSecBrush;

            g.DrawString(line.c_str(), -1, fontMono, PointF((float)x + gutter_w + 12, (float)line_y), lineBrush);

            // Minimap pixel line
            Pen miniPen(Color(0x60, 0x8B, 0x5C, 0xF6), 1.0f);
            g.DrawLine(&miniPen, x + w - minimap_w + 8, line_y + 4, x + w - 8, line_y + 4);

            line_y += 18;
        }
    }
}

// Master GDI+ Celeslib Frame Renderer
void RenderCeleslibFrame(Gdiplus::Graphics& g, int width, int height, const AppState& state) {
    using namespace Gdiplus;
    g.SetSmoothingMode(SmoothingModeAntiAlias);
    g.SetTextRenderingHint(TextRenderingHintClearTypeGridFit);

    const Strings& s = GetStrings(state.ui_lang);

    // 1. Background
    SolidBrush bgBrush(Theme::BgCanvas);
    g.FillRectangle(&bgBrush, 0, 0, width, height);

    // 2. Custom Dark Header (Y: 0..48)
    SolidBrush headerBrush(Theme::BgHeader);
    g.FillRectangle(&headerBrush, 0, 0, width, 48);

    Pen borderPen(Theme::BorderDark, 1.0f);
    Pen borderHoverPen(Theme::BorderHover, 1.0f);
    g.DrawLine(&borderPen, 0, 48, width, 48);

    // 2a. Celeslib Star Logo
    Bitmap logoBmp(CELESLIB_LOGO_32_BGRA_WIDTH, CELESLIB_LOGO_32_BGRA_HEIGHT,
                   CELESLIB_LOGO_32_BGRA_WIDTH * 4, PixelFormat32bppARGB,
                   (BYTE*)CELESLIB_LOGO_32_BGRA);
    g.DrawImage(&logoBmp, 16, 8, 32, 32);

    // 2b. Title & Version Badges
    FontFamily sansFamily(L"Segoe UI");
    Font fontTitle(&sansFamily, 13, FontStyleBold, UnitPixel);
    Font fontBadge(&sansFamily, 10, FontStyleRegular, UnitPixel);
    Font fontRegular(&sansFamily, 11, FontStyleRegular, UnitPixel);
    Font fontMono(L"Consolas", 11, FontStyleRegular, UnitPixel);

    SolidBrush textPrimaryBrush(Theme::TextPrimary);
    SolidBrush textSecBrush(Theme::TextSecondary);
    SolidBrush textMutedBrush(Theme::TextMuted);
    SolidBrush accentBrush(Theme::AccentViolet);
    SolidBrush accentLightBrush(Theme::AccentLight);
    SolidBrush pillDarkBg(Theme::BgPill);
    SolidBrush pillHoverBg(Theme::BgPillHover);
    SolidBrush pillVioletBg(Color(0x33, 0x8B, 0x5C, 0xF6));
    Pen pillVioletBorder(Theme::AccentViolet, 1.0f);

    g.DrawString(s.app_name, -1, &fontTitle, PointF(56, 15), &textPrimaryBrush);

    // Version Badge [ v1.0.0 ]
    FillRoundRect(g, pillVioletBg, 122, 14, 52, 20, 4);
    DrawRoundRect(g, pillVioletBorder, 122, 14, 52, 20, 4);
    g.DrawString(s.version_badge, -1, &fontBadge, PointF(128, 17), &accentLightBrush);

    // Game Build Badge [ Game Build 1.4.12 ]
    FillRoundRect(g, pillDarkBg, 182, 14, 118, 20, 4);
    DrawRoundRect(g, borderPen, 182, 14, 118, 20, 4);
    g.DrawString(s.game_badge, -1, &fontBadge, PointF(190, 17), &textSecBrush);

    // 2c. Header Quick Toggles
    // UI Language Toggle (button index 100)
    bool ui_hover = (state.hovered_btn == 100);
    const wchar_t* ui_toggle_txt = (state.ui_lang == UiLang::EN) ? s.toggle_ui_en : s.toggle_ui_id;
    FillRoundRect(g, ui_hover ? pillHoverBg : pillDarkBg, width - 360, 12, 95, 24, 6);
    DrawRoundRect(g, ui_hover ? borderHoverPen : borderPen, width - 360, 12, 95, 24, 6);
    // Vector globe dot
    SolidBrush globeDotBrush(Color(0xFF, 0x60, 0xA5, 0xFA));
    g.FillEllipse(&globeDotBrush, width - 352, 19, 8, 8);
    g.DrawString(ui_toggle_txt, -1, &fontRegular, PointF(width - 340, 16), &textPrimaryBrush);

    // Patch Mode Toggle (button index 101)
    bool mode_hover = (state.hovered_btn == 101);
    const wchar_t* mode_toggle_txt = (state.patch_mode == PatchMode::EN_FULL) ? s.toggle_mode_en : s.toggle_mode_id;
    FillRoundRect(g, mode_hover ? pillHoverBg : pillDarkBg, width - 255, 12, 145, 24, 6);
    DrawRoundRect(g, mode_hover ? borderHoverPen : borderPen, width - 255, 12, 145, 24, 6);
    // Vector target dot
    SolidBrush targetDotBrush(Theme::AccentViolet);
    g.FillEllipse(&targetDotBrush, width - 247, 19, 8, 8);
    g.DrawString(mode_toggle_txt, -1, &fontRegular, PointF(width - 235, 16), &textPrimaryBrush);

    // Window Controls [—] [□] [×]
    g.DrawString(L"—", -1, &fontRegular, PointF(width - 80, 14), (state.hovered_btn == 102) ? &textPrimaryBrush : &textSecBrush);
    g.DrawString(L"□", -1, &fontRegular, PointF(width - 55, 14), (state.hovered_btn == 103) ? &textPrimaryBrush : &textSecBrush);
    g.DrawString(L"×", -1, &fontRegular, PointF(width - 30, 14), (state.hovered_btn == 104) ? &textPrimaryBrush : &textSecBrush);

    // 3. Left Sidebar (Dynamic width: collapsed = 48, expanded = 170)
    int sidebar_w = state.sidebar_collapsed ? 48 : 170;
    SolidBrush sidebarBrush(Theme::BgSidebar);
    g.FillRectangle(&sidebarBrush, 0, 49, sidebar_w, height - 49);
    g.DrawLine(&borderPen, sidebar_w, 49, sidebar_w, height);

    // Collapse toggle button (button index 200)
    bool col_hover = (state.hovered_btn == 200);
    FillRoundRect(g, col_hover ? pillHoverBg : pillDarkBg, 10, 56, sidebar_w - 20, 24, 4);
    DrawRoundRect(g, col_hover ? borderHoverPen : borderPen, 10, 56, sidebar_w - 20, 24, 4);
    const wchar_t* col_icon = state.sidebar_collapsed ? L">" : L"<";
    g.DrawString(col_icon, -1, &fontBadge, PointF((float)(sidebar_w / 2 - 4), 60), &textSecBrush);

    // Sidebar navigation tabs
    struct NavItem {
        NavView view;
        const wchar_t* label;
        const wchar_t* short_label;
        int y;
        int btn_id;
    };
    NavItem nav_items[] = {
        { NavView::Dashboard, s.nav_dashboard, L"DB", 90, 201 },
        { NavView::Patcher, s.nav_patcher, L"PC", 130, 202 },
        { NavView::Android, s.nav_android, L"AD", 170, 203 },
        { NavView::Settings, s.nav_settings, L"ST", 210, 204 }
    };

    for (const auto& item : nav_items) {
        bool is_active = (state.current_view == item.view);
        bool is_hover = (state.hovered_btn == item.btn_id);
        int tab_x = 8;
        int tab_w = sidebar_w - 16;
        if (is_active) {
            FillRoundRect(g, pillVioletBg, (float)tab_x, (float)item.y, (float)tab_w, 32, 6);
            DrawRoundRect(g, pillVioletBorder, (float)tab_x, (float)item.y, (float)tab_w, 32, 6);
            if (state.sidebar_collapsed) {
                g.DrawString(item.short_label, -1, &fontBadge, PointF((float)tab_x + 8, (float)item.y + 8), &textPrimaryBrush);
            } else {
                g.DrawString(item.label, -1, &fontRegular, PointF((float)tab_x + 14, (float)item.y + 7), &textPrimaryBrush);
            }
        } else {
            if (is_hover) {
                FillRoundRect(g, pillHoverBg, (float)tab_x, (float)item.y, (float)tab_w, 32, 6);
                DrawRoundRect(g, borderHoverPen, (float)tab_x, (float)item.y, (float)tab_w, 32, 6);
            }
            if (state.sidebar_collapsed) {
                g.DrawString(item.short_label, -1, &fontBadge, PointF((float)tab_x + 8, (float)item.y + 8), &textSecBrush);
            } else {
                g.DrawString(item.label, -1, &fontRegular, PointF((float)tab_x + 14, (float)item.y + 7), &textSecBrush);
            }
        }
    }

    // Sidebar Bottom Copyright
    if (!state.sidebar_collapsed) {
        g.DrawString(L"Celeslib v1.0.0", -1, &fontBadge, PointF(16, (float)height - 40), &textMutedBrush);
        g.DrawString(L"Game Build 1.4.12", -1, &fontBadge, PointF(16, (float)height - 25), &textMutedBrush);
    }

    // 4. Main Body Content
    int main_x = sidebar_w + 16;
    int main_w = width - main_x - 16;

    if (state.current_view == NavView::Patcher) {
        // 4a. Top Pill Action Toolbar
        struct ActionBtn {
            int id;
            const wchar_t* label;
            int w;
            bool highlight;
        };
        ActionBtn actions[] = {
            { 1, s.btn_install, 120, true },
            { 2, s.btn_restore, 115, false },
            { 3, s.btn_verify, 110, false },
            { 4, s.btn_browse, 110, false },
            { 5, s.btn_autodetect, 105, false },
            { 6, s.btn_clear, 90, false }
        };

        int cur_x = main_x;
        for (const auto& btn : actions) {
            bool btn_hover = (state.hovered_btn == btn.id);
            if (btn.highlight) {
                SolidBrush installBg(btn_hover ? Color(0xFF, 0x8B, 0x5C, 0xF6) : Color(0xFF, 0x7C, 0x3A, 0xED));
                FillRoundRect(g, installBg, (float)cur_x, 62, (float)btn.w, 32, 6);
                g.DrawString(btn.label, -1, &fontRegular, PointF((float)cur_x + 10, 69), &textPrimaryBrush);
            } else {
                FillRoundRect(g, btn_hover ? pillHoverBg : pillDarkBg, (float)cur_x, 62, (float)btn.w, 32, 6);
                DrawRoundRect(g, btn_hover ? borderHoverPen : borderPen, (float)cur_x, 62, (float)btn.w, 32, 6);
                g.DrawString(btn.label, -1, &fontRegular, PointF((float)cur_x + 10, 69), &textSecBrush);
            }
            cur_x += btn.w + 8;
        }

        // 4b. Game Path & Status Bar
        int bar_y = 104;
        FillRoundRect(g, pillDarkBg, (float)main_x, (float)bar_y, (float)main_w, 32, 6);
        DrawRoundRect(g, borderPen, (float)main_x, (float)bar_y, (float)main_w, 32, 6);

        std::wstring path_display = std::wstring(s.console_game_path_label) + L" " +
            (state.game_dir.empty() ? L"C:\\Program Files\\WXQLauncher\\WXQ (Auto-Detected)" : state.game_dir);
        g.DrawString(path_display.c_str(), -1, &fontRegular, PointF((float)main_x + 12, (float)bar_y + 8), &textSecBrush);

        // Status pill badge on right
        SolidBrush statusBrush(state.status_color);
        SolidBrush bgCanvasBrush(Theme::BgCanvas);
        int badge_w = 110;
        int badge_x = main_x + main_w - badge_w - 6;
        FillRoundRect(g, bgCanvasBrush, (float)badge_x, (float)bar_y + 4, (float)badge_w, 24, 4);
        DrawRoundRect(g, borderPen, (float)badge_x, (float)bar_y + 4, (float)badge_w, 24, 4);
        g.FillEllipse(&statusBrush, badge_x + 8, bar_y + 12, 8, 8);
        g.DrawString(state.status_text.c_str(), -1, &fontBadge, PointF((float)badge_x + 22, (float)bar_y + 8), &textPrimaryBrush);

        // 4c. Editor-Style Line-Numbered Monospace Console
        int con_y = 146;
        int con_h = height - con_y - 16;
        RenderConsolePanel(g, main_x, con_y, main_w, con_h, state,
                           &fontMono, &textMutedBrush, &textPrimaryBrush,
                           &accentLightBrush, (SolidBrush*)&accentBrush, &textSecBrush);
    } else if (state.current_view == NavView::Settings) {
        // Settings Card View
        int card_y = 70;

        // Card 1: UI Language
        FillRoundRect(g, pillDarkBg, (float)main_x, (float)card_y, (float)main_w, 88, 6);
        DrawRoundRect(g, borderPen, (float)main_x, (float)card_y, (float)main_w, 88, 6);
        g.DrawString(s.settings_ui_lang_title, -1, &fontTitle, PointF((float)main_x + 16, (float)card_y + 14), &textPrimaryBrush);
        g.DrawString(s.settings_ui_lang_desc, -1, &fontRegular, PointF((float)main_x + 16, (float)card_y + 36), &textSecBrush);

        // Buttons for UI Lang
        SolidBrush activePill(Color(0xFF, 0x7C, 0x3A, 0xED));
        FillRoundRect(g, (state.ui_lang == UiLang::ID ? activePill : pillDarkBg), (float)main_x + 16, (float)card_y + 54, 140, 24, 4);
        g.DrawString(L"Bahasa Indonesia", -1, &fontBadge, PointF((float)main_x + 24, (float)card_y + 58), &textPrimaryBrush);

        FillRoundRect(g, (state.ui_lang == UiLang::EN ? activePill : pillDarkBg), (float)main_x + 166, (float)card_y + 54, 120, 24, 4);
        g.DrawString(L"English", -1, &fontBadge, PointF((float)main_x + 180, (float)card_y + 58), &textPrimaryBrush);

        // Card 2: Patch Mode
        card_y += 104;
        FillRoundRect(g, pillDarkBg, (float)main_x, (float)card_y, (float)main_w, 98, 6);
        DrawRoundRect(g, borderPen, (float)main_x, (float)card_y, (float)main_w, 98, 6);
        g.DrawString(s.settings_patch_mode_title, -1, &fontTitle, PointF((float)main_x + 16, (float)card_y + 14), &textPrimaryBrush);
        g.DrawString(s.settings_patch_mode_desc, -1, &fontRegular, PointF((float)main_x + 16, (float)card_y + 36), &textSecBrush);

        FillRoundRect(g, (state.patch_mode == PatchMode::ID_HYBRID ? activePill : pillDarkBg), (float)main_x + 16, (float)card_y + 60, 180, 26, 4);
        g.DrawString(L"Indonesian Hybrid (ID)", -1, &fontBadge, PointF((float)main_x + 24, (float)card_y + 65), &textPrimaryBrush);

        FillRoundRect(g, (state.patch_mode == PatchMode::EN_FULL ? activePill : pillDarkBg), (float)main_x + 206, (float)card_y + 60, 160, 26, 4);
        g.DrawString(L"Full English (EN)", -1, &fontBadge, PointF((float)main_x + 220, (float)card_y + 65), &textPrimaryBrush);

        // Card 3: Game Directory
        card_y += 114;
        FillRoundRect(g, pillDarkBg, (float)main_x, (float)card_y, (float)main_w, 80, 6);
        DrawRoundRect(g, borderPen, (float)main_x, (float)card_y, (float)main_w, 80, 6);
        g.DrawString(s.settings_game_dir_title, -1, &fontTitle, PointF((float)main_x + 16, (float)card_y + 14), &textPrimaryBrush);
        g.DrawString(s.settings_game_dir_desc, -1, &fontRegular, PointF((float)main_x + 16, (float)card_y + 36), &textSecBrush);
        g.DrawString(state.game_dir.empty() ? L"C:\\Program Files\\WXQLauncher\\WXQ" : state.game_dir.c_str(),
                     -1, &fontMono, PointF((float)main_x + 16, (float)card_y + 54), &accentLightBrush);
    } else if (state.current_view == NavView::Android) {
        // Android USB View with 3 functional buttons and live console
        FillRoundRect(g, pillDarkBg, (float)main_x, 70, (float)main_w, 160, 6);
        DrawRoundRect(g, borderPen, (float)main_x, 70, (float)main_w, 160, 6);
        g.DrawString(s.android_title, -1, &fontTitle, PointF((float)main_x + 16, 86), &textPrimaryBrush);
        g.DrawString(s.android_desc, -1, &fontRegular, PointF((float)main_x + 16, 114), &textSecBrush);

        SolidBrush activePill(Color(0xFF, 0x7C, 0x3A, 0xED));
        // Button 1: Scan Device (button index 301)
        bool scan_hover = (state.hovered_btn == 301);
        FillRoundRect(g, scan_hover ? pillVioletBg : activePill, (float)main_x + 16, 150, 140, 32, 6);
        g.DrawString(s.android_btn_scan, -1, &fontRegular, PointF((float)main_x + 28, 157), &textPrimaryBrush);

        // Button 2: Patch Android (button index 302)
        bool patch_hover = (state.hovered_btn == 302);
        FillRoundRect(g, patch_hover ? pillHoverBg : pillDarkBg, (float)main_x + 166, 150, 150, 32, 6);
        DrawRoundRect(g, patch_hover ? borderHoverPen : borderPen, (float)main_x + 166, 150, 150, 32, 6);
        g.DrawString(s.android_btn_patch, -1, &fontRegular, PointF((float)main_x + 180, 157), &textSecBrush);

        // Button 3: Recover Android (button index 303)
        bool rec_hover = (state.hovered_btn == 303);
        FillRoundRect(g, rec_hover ? pillHoverBg : pillDarkBg, (float)main_x + 326, 150, 150, 32, 6);
        DrawRoundRect(g, rec_hover ? borderHoverPen : borderPen, (float)main_x + 326, 150, 150, 32, 6);
        g.DrawString(s.android_btn_recover, -1, &fontRegular, PointF((float)main_x + 340, 157), &textSecBrush);

        // Live Diagnostic Console Panel below Android card (con_y = 244)
        int con_y = 244;
        int con_h = height - con_y - 16;
        RenderConsolePanel(g, main_x, con_y, main_w, con_h, state,
                           &fontMono, &textMutedBrush, &textPrimaryBrush,
                           &accentLightBrush, (SolidBrush*)&accentBrush, &textSecBrush);
    } else if (state.current_view == NavView::Dashboard) {
        // Dashboard Overview
        FillRoundRect(g, pillDarkBg, (float)main_x, 70, (float)main_w, 180, 6);
        DrawRoundRect(g, borderPen, (float)main_x, 70, (float)main_w, 180, 6);
        g.DrawString(s.app_title, -1, &fontTitle, PointF((float)main_x + 16, 86), &textPrimaryBrush);
        g.DrawString(s.sub_header, -1, &fontRegular, PointF((float)main_x + 16, 110), &textSecBrush);

        std::wstring build_info = L"Engine Target: Honor of Kings: Ace Build 1.4.12 | Celeslib Native Release v1.0.0";
        g.DrawString(build_info.c_str(), -1, &fontRegular, PointF((float)main_x + 16, 134), &accentLightBrush);

        g.DrawString(s.copyright_label, -1, &fontBadge, PointF((float)main_x + 16, 210), &textMutedBrush);
    }
}

// Window Procedure
LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
        case WM_NCCALCSIZE: {
            if (wParam == TRUE) {
                return 0; // True Frameless Window: client area covers whole window
            }
            break;
        }

        case WM_CREATE: {
            // Enable Dark Titlebar Mode via DWM
            BOOL darkMode = TRUE;
            DwmSetWindowAttribute(hwnd, 20, &darkMode, sizeof(darkMode)); // DWMWA_USE_IMMERSIVE_DARK_MODE
            return 0;
        }

        case WM_MOUSEMOVE: {
            int x = GET_X_LPARAM(lParam);
            int y = GET_Y_LPARAM(lParam);

            int new_hover = -1;
            int sidebar_w = g_state.sidebar_collapsed ? 48 : 170;
            int main_x = sidebar_w + 16;

            if (y >= 12 && y <= 36) {
                if (x >= g_state.width - 360 && x <= g_state.width - 265) new_hover = 100;
                else if (x >= g_state.width - 255 && x <= g_state.width - 110) new_hover = 101;
                else if (x >= g_state.width - 90 && x <= g_state.width - 68) new_hover = 102;
                else if (x >= g_state.width - 65 && x <= g_state.width - 40) new_hover = 103;
                else if (x >= g_state.width - 38 && x <= g_state.width - 10) new_hover = 104;
            } else if (x <= sidebar_w) {
                if (y >= 56 && y <= 80) new_hover = 200;
                else if (y >= 90 && y <= 122) new_hover = 201;
                else if (y >= 130 && y <= 162) new_hover = 202;
                else if (y >= 170 && y <= 202) new_hover = 203;
                else if (y >= 210 && y <= 242) new_hover = 204;
            } else if (g_state.current_view == NavView::Patcher && y >= 62 && y <= 94) {
                int cur_x = main_x;
                if (x >= cur_x && x <= cur_x + 120) new_hover = 1;
                else if (x >= cur_x + 128 && x <= cur_x + 243) new_hover = 2;
                else if (x >= cur_x + 251 && x <= cur_x + 361) new_hover = 3;
                else if (x >= cur_x + 369 && x <= cur_x + 479) new_hover = 4;
                else if (x >= cur_x + 487 && x <= cur_x + 592) new_hover = 5;
                else if (x >= cur_x + 600 && x <= cur_x + 690) new_hover = 6;
            } else if (g_state.current_view == NavView::Android && y >= 150 && y <= 182) {
                if (x >= main_x + 16 && x <= main_x + 156) new_hover = 301;
                else if (x >= main_x + 166 && x <= main_x + 316) new_hover = 302;
                else if (x >= main_x + 326 && x <= main_x + 476) new_hover = 303;
            }

            if (new_hover != g_state.hovered_btn) {
                g_state.hovered_btn = new_hover;
                InvalidateRect(hwnd, NULL, FALSE);
            }

            TRACKMOUSEEVENT tme = { sizeof(tme), TME_LEAVE, hwnd, 0 };
            TrackMouseEvent(&tme);
            return 0;
        }

        case WM_MOUSELEAVE: {
            if (g_state.hovered_btn != -1) {
                g_state.hovered_btn = -1;
                InvalidateRect(hwnd, NULL, FALSE);
            }
            return 0;
        }

        case WM_LBUTTONDOWN: {
            int x = GET_X_LPARAM(lParam);
            int y = GET_Y_LPARAM(lParam);
            int sidebar_w = g_state.sidebar_collapsed ? 48 : 170;
            int main_x = sidebar_w + 16;

            // Header Toggles & Window Controls
            if (y >= 12 && y <= 36) {
                // UI Toggle
                if (x >= g_state.width - 360 && x <= g_state.width - 265) {
                    g_state.ui_lang = (g_state.ui_lang == UiLang::ID) ? UiLang::EN : UiLang::ID;
                    SaveConfig();
                    InvalidateRect(hwnd, NULL, FALSE);
                    return 0;
                }
                // Patch Mode Toggle
                if (x >= g_state.width - 255 && x <= g_state.width - 110) {
                    g_state.patch_mode = (g_state.patch_mode == PatchMode::ID_HYBRID) ? PatchMode::EN_FULL : PatchMode::ID_HYBRID;
                    SaveConfig();
                    InvalidateRect(hwnd, NULL, FALSE);
                    return 0;
                }
            }

            // Window Controls [—] [□] [×]
            if (y >= 8 && y <= 36) {
                if (x >= g_state.width - 90 && x <= g_state.width - 68) {
                    ShowWindow(hwnd, SW_MINIMIZE);
                    return 0;
                }
                if (x >= g_state.width - 65 && x <= g_state.width - 40) {
                    WINDOWPLACEMENT wp = { sizeof(wp) };
                    GetWindowPlacement(hwnd, &wp);
                    if (wp.showCmd == SW_MAXIMIZE) {
                        ShowWindow(hwnd, SW_RESTORE);
                    } else {
                        ShowWindow(hwnd, SW_MAXIMIZE);
                    }
                    return 0;
                }
                if (x >= g_state.width - 38 && x <= g_state.width - 10) {
                    PostQuitMessage(0);
                    return 0;
                }
            }

            // Drag window on empty header space
            if (y < 48 && x < g_state.width - 365) {
                ReleaseCapture();
                SendMessageW(hwnd, WM_NCLBUTTONDOWN, HTCAPTION, 0);
                return 0;
            }

            // Sidebar Controls
            if (x <= sidebar_w) {
                // Collapse toggle
                if (y >= 56 && y <= 80) {
                    g_state.sidebar_collapsed = !g_state.sidebar_collapsed;
                    SaveConfig();
                    InvalidateRect(hwnd, NULL, FALSE);
                    return 0;
                }
                // Nav items
                if (y >= 90 && y <= 122) { g_state.current_view = NavView::Dashboard; InvalidateRect(hwnd, NULL, FALSE); return 0; }
                if (y >= 130 && y <= 162) { g_state.current_view = NavView::Patcher; InvalidateRect(hwnd, NULL, FALSE); return 0; }
                if (y >= 170 && y <= 202) { g_state.current_view = NavView::Android; InvalidateRect(hwnd, NULL, FALSE); return 0; }
                if (y >= 210 && y <= 242) { g_state.current_view = NavView::Settings; InvalidateRect(hwnd, NULL, FALSE); return 0; }
            }

            // Patcher Action Toolbar Buttons
            if (g_state.current_view == NavView::Patcher && y >= 62 && y <= 94) {
                int cur_x = main_x;
                const Strings& s = GetStrings(g_state.ui_lang);

                // 1. Install
                if (x >= cur_x && x <= cur_x + 120) {
                    if (MessageBoxW(hwnd, s.confirm_install_msg, s.confirm_install_title, MB_YESNO | MB_ICONQUESTION) == IDYES) {
                        ExecuteWorkerAction(L"install", g_state.game_dir);
                    }
                    return 0;
                }
                cur_x += 128;

                // 2. Restore
                if (x >= cur_x && x <= cur_x + 115) {
                    if (MessageBoxW(hwnd, s.confirm_restore_msg, s.confirm_restore_title, MB_YESNO | MB_ICONQUESTION) == IDYES) {
                        ExecuteWorkerAction(L"restore", g_state.game_dir);
                    }
                    return 0;
                }
                cur_x += 123;

                // 3. Verify
                if (x >= cur_x && x <= cur_x + 110) {
                    ExecuteWorkerAction(L"status", g_state.game_dir);
                    return 0;
                }
                cur_x += 118;

                // 4. Browse Folder
                if (x >= cur_x && x <= cur_x + 110) {
                    BROWSEINFOW bi = { 0 };
                    bi.lpszTitle = s.btn_browse;
                    bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE;
                    LPITEMIDLIST pidl = SHBrowseForFolderW(&bi);
                    if (pidl) {
                        wchar_t path[MAX_PATH];
                        if (SHGetPathFromIDListW(pidl, path)) {
                            g_state.game_dir = path;
                            AppendLog(L"[INFO] Direktori game dipilih: " + g_state.game_dir);
                            InvalidateRect(hwnd, NULL, FALSE);
                        }
                        CoTaskMemFree(pidl);
                    }
                    return 0;
                }
                cur_x += 118;

                // 5. Auto-Detect
                if (x >= cur_x && x <= cur_x + 105) {
                    ExecuteWorkerAction(L"discover", L"");
                    return 0;
                }
                cur_x += 113;

                // 6. Clear
                if (x >= cur_x && x <= cur_x + 90) {
                    std::lock_guard<std::mutex> lock(g_state.mtx);
                    g_state.log_lines.clear();
                    InvalidateRect(hwnd, NULL, FALSE);
                    return 0;
                }
            }

            // Android USB Action Buttons
            if (g_state.current_view == NavView::Android && y >= 150 && y <= 182) {
                if (x >= main_x + 16 && x <= main_x + 156) {
                    ExecuteMobileWorkerAction(L"devices");
                    return 0;
                }
                if (x >= main_x + 166 && x <= main_x + 316) {
                    ExecuteMobileWorkerAction(L"patch");
                    return 0;
                }
                if (x >= main_x + 326 && x <= main_x + 476) {
                    ExecuteMobileWorkerAction(L"recover");
                    return 0;
                }
            }

            // Settings interactive toggles
            if (g_state.current_view == NavView::Settings) {
                // UI Lang buttons (Y: 124..148)
                if (y >= 124 && y <= 148) {
                    if (x >= main_x + 16 && x <= main_x + 156) {
                        g_state.ui_lang = UiLang::ID;
                        SaveConfig();
                        InvalidateRect(hwnd, NULL, FALSE);
                        return 0;
                    }
                    if (x >= main_x + 166 && x <= main_x + 286) {
                        g_state.ui_lang = UiLang::EN;
                        SaveConfig();
                        InvalidateRect(hwnd, NULL, FALSE);
                        return 0;
                    }
                }
                // Patch Mode buttons (Y: 234..260)
                if (y >= 234 && y <= 260) {
                    if (x >= main_x + 16 && x <= main_x + 196) {
                        g_state.patch_mode = PatchMode::ID_HYBRID;
                        SaveConfig();
                        InvalidateRect(hwnd, NULL, FALSE);
                        return 0;
                    }
                    if (x >= main_x + 206 && x <= main_x + 366) {
                        g_state.patch_mode = PatchMode::EN_FULL;
                        SaveConfig();
                        InvalidateRect(hwnd, NULL, FALSE);
                        return 0;
                    }
                }
            }

            return 0;
        }

        case WM_SIZE: {
            g_state.width = LOWORD(lParam);
            g_state.height = HIWORD(lParam);
            InvalidateRect(hwnd, NULL, FALSE);
            return 0;
        }

        case WM_PAINT: {
            PAINTSTRUCT ps;
            HDC hdc = BeginPaint(hwnd, &ps);

            RECT rc;
            GetClientRect(hwnd, &rc);
            int w = rc.right - rc.left;
            int h = rc.bottom - rc.top;

            // Double buffering
            HDC memDC = CreateCompatibleDC(hdc);
            HBITMAP memBitmap = CreateCompatibleBitmap(hdc, w, h);
            HGDIOBJ oldBitmap = SelectObject(memDC, memBitmap);

            {
                Gdiplus::Graphics g(memDC);
                RenderCeleslibFrame(g, w, h, g_state);
            }

            BitBlt(hdc, 0, 0, w, h, memDC, 0, 0, SRCCOPY);

            SelectObject(memDC, oldBitmap);
            DeleteObject(memBitmap);
            DeleteDC(memDC);

            EndPaint(hwnd, &ps);
            return 0;
        }

        case WM_ERASEBKGND:
            return 1; // Prevent flicker

        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;
    }
    return DefWindowProcW(hwnd, msg, wParam, lParam);
}

// Offscreen PNG Smoke UI Exporter
int RenderOffscreenPreview(const std::wstring& out_png_path, UiLang ui_lang, PatchMode mode, NavView view) {
    using namespace Gdiplus;
    int w = 980, h = 620;
    Bitmap bmp(w, h, PixelFormat32bppARGB);
    {
        Graphics g(&bmp);
        AppState state;
        state.ui_lang = ui_lang;
        state.patch_mode = mode;
        state.current_view = view;
        state.width = w;
        state.height = h;
        state.sidebar_collapsed = false;
        state.game_dir = L"C:\\Program Files\\WXQLauncher\\WXQ";
        state.log_lines = {
            L"[INFO] Menemukan instalasi Honor of Kings: Ace (Build 1.4.12)",
            L"[OK] Verifikasi integritas 508 tabel protoc berhasil.",
            L"[OK] Celeslib Dual-State Engine siap beroperasi.",
            L"[OK] Siap memasang patch Bahasa Indonesia."
        };
        RenderCeleslibFrame(g, w, h, state);
    }

    // CLSID for PNG encoder: {557CF406-1A04-11D3-9A73-0000F81EF32E}
    CLSID pngClsid = { 0x557cf406, 0x1a04, 0x11d3, { 0x9a, 0x73, 0x00, 0x00, 0xf8, 0x1e, 0xf3, 0x2e } };
    Status st = bmp.Save(out_png_path.c_str(), &pngClsid, NULL);
    return (st == Ok) ? 0 : 1;
}

// Entry Point
int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPWSTR lpCmdLine, int nCmdShow) {
    Gdiplus::GdiplusStartupInput gdiplusStartupInput;
    ULONG_PTR gdiplusToken;
    Gdiplus::GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);

    int argc = 0;
    LPWSTR* argv = CommandLineToArgvW(GetCommandLineW(), &argc);

    // Check CLI flags
    for (int i = 1; i < argc; ++i) {
        std::wstring arg = argv[i];
        if (arg == L"--smoke-ui" && i + 1 < argc) {
            std::wstring out_dir = argv[i + 1];
            RenderOffscreenPreview(out_dir + L"\\celeslib_patcher_id.png", UiLang::ID, PatchMode::ID_HYBRID, NavView::Patcher);
            RenderOffscreenPreview(out_dir + L"\\celeslib_patcher_en.png", UiLang::EN, PatchMode::EN_FULL, NavView::Patcher);
            RenderOffscreenPreview(out_dir + L"\\celeslib_dashboard_id.png", UiLang::ID, PatchMode::ID_HYBRID, NavView::Dashboard);
            RenderOffscreenPreview(out_dir + L"\\celeslib_settings_id.png", UiLang::ID, PatchMode::ID_HYBRID, NavView::Settings);
            Gdiplus::GdiplusShutdown(gdiplusToken);
            return 0;
        }
        if (arg == L"--verify-bundle") {
            std::wstring worker;
            bool ok = LocateAndExtractWorker(worker);
            Gdiplus::GdiplusShutdown(gdiplusToken);
            return ok ? 0 : 2;
        }
        if (arg == L"--self-test") {
            std::wstring worker;
            if (!LocateAndExtractWorker(worker)) {
                Gdiplus::GdiplusShutdown(gdiplusToken);
                return 2;
            }
            std::wstring work_dir = GetCeleslibAppDataDir() + L"\\work";
            CreateDirectoryW(work_dir.c_str(), NULL);
            std::wstring res_path = work_dir + L"\\result.json";
            std::wstringstream cmd;
            cmd << L"\"" << worker << L"\" self-test --work \"" << work_dir << L"\" --result \"" << res_path << L"\"";
            std::wstring out;
            int ret = RunWorkerProcessSync(cmd.str(), out);
            Gdiplus::GdiplusShutdown(gdiplusToken);
            return ret;
        }
        if (arg == L"--status" || arg == L"--install" || arg == L"--restore" || arg == L"--discover") {
            std::wstring worker;
            if (!LocateAndExtractWorker(worker)) {
                Gdiplus::GdiplusShutdown(gdiplusToken);
                return 2;
            }
            std::wstring action = arg.substr(2); // strip "--"
            std::wstring work_dir = GetCeleslibAppDataDir() + L"\\work";
            CreateDirectoryW(work_dir.c_str(), NULL);
            std::wstring res_path = work_dir + L"\\result.json";
            std::wstringstream cmd;
            cmd << L"\"" << worker << L"\" " << action << L" --work \"" << work_dir << L"\" --result \"" << res_path << L"\"";
            for (int j = i + 1; j < argc; ++j) {
                if (std::wstring(argv[j]) == L"--game-dir" && j + 1 < argc) {
                    cmd << L" --game-dir \"" << argv[j + 1] << L"\"";
                    j++;
                }
            }
            std::wstring out;
            int ret = RunWorkerProcessSync(cmd.str(), out);
            Gdiplus::GdiplusShutdown(gdiplusToken);
            return ret;
        }
    }

    LoadConfig();

    WNDCLASSEXW wc = { sizeof(wc) };
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = L"CeleslibPatcherUI";
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hIcon = LoadIconW(hInstance, MAKEINTRESOURCEW(1));
    RegisterClassExW(&wc);

    HWND hwnd = CreateWindowExW(
        WS_EX_APPWINDOW,
        wc.lpszClassName,
        L"Celeslib Honor of Kings: Ace Patcher",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, 980, 620,
        NULL, NULL, hInstance, NULL
    );

    g_hwnd = hwnd;
    ShowWindow(hwnd, nCmdShow);
    UpdateWindow(hwnd);

    // Initial check for installation
    AppendLog(L"[INFO] Celeslib Honor of Kings: Ace Patcher v1.0.0 siap.");
    AppendLog(L"[INFO] Mode Patch Aktif: " + std::wstring(g_state.patch_mode == PatchMode::EN_FULL ? L"Full English (EN)" : L"Indonesian Hybrid (ID)"));

    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    Gdiplus::GdiplusShutdown(gdiplusToken);
    return (int)msg.wParam;
}
