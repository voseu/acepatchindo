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

// Color Palette - Single-Page Monochrome Obsidian System
namespace Theme {
    static const Gdiplus::Color BgCanvas(0xFF, 0x09, 0x09, 0x09);       // #090909 Main Obsidian Canvas
    static const Gdiplus::Color CardSurface(0xFF, 0x0D, 0x0D, 0x0D);    // #0D0D0D Cards / Toolbars
    static const Gdiplus::Color CardSurfaceElevated(0xFF, 0x11, 0x11, 0x11); // #111111 Elevated elements
    static const Gdiplus::Color InputSurface(0xFF, 0x05, 0x05, 0x05);   // #050505 Input boxes & Tracks
    static const Gdiplus::Color BorderDark(0xFF, 0x33, 0x33, 0x33);     // #333333 Crisp borders
    static const Gdiplus::Color BorderSubtle(0xFF, 0x26, 0x26, 0x26);   // #262626 Subtle dividers
    static const Gdiplus::Color BorderFaint(0xFF, 0x1E, 0x1E, 0x1E);    // #1E1E1E Gutter/Minimap rails
    static const Gdiplus::Color BorderHover(0xFF, 0x55, 0x55, 0x55);    // #555555 Button Hover Border
    static const Gdiplus::Color PrimaryWhite(0xFF, 0xFF, 0xFF, 0xFF);   // #FFFFFF Active Segments & CTA Fill
    static const Gdiplus::Color PrimaryBlack(0xFF, 0x00, 0x00, 0x00);   // #000000 Active CTA Text
    static const Gdiplus::Color TextWhite(0xFF, 0xFF, 0xFF, 0xFF);      // #FFFFFF Primary Headings
    static const Gdiplus::Color TextLight(0xFF, 0xE5, 0xE5, 0xE5);      // #E5E5E5 High readable text
    static const Gdiplus::Color TextSilver(0xFF, 0xCC, 0xCC, 0xCC);     // #CCCCCC Secondary labels
    static const Gdiplus::Color TextMuted(0xFF, 0x88, 0x88, 0x88);      // #888888 Muted descriptions
    static const Gdiplus::Color TextSubtle(0xFF, 0x77, 0x77, 0x77);     // #777777 Card footers
    static const Gdiplus::Color TextFaint(0xFF, 0x55, 0x55, 0x55);      // #555555 Line numbers
    static const Gdiplus::Color AccentGreen(0xFF, 0x22, 0xC5, 0x5E);    // #22C55E Glowing status OK / [OK]
    static const Gdiplus::Color AccentRed(0xFF, 0xEF, 0x44, 0x44);      // #EF4444 Error / Restore hover
    static const Gdiplus::Color AccentYellow(0xFF, 0xEA, 0xB3, 0x08);   // #EAB308 Working status
    static const Gdiplus::Color CloseHoverBg(0xFF, 0x4A, 0x00, 0x00);   // #4A0000 Close button hover
    static const Gdiplus::Color SecondaryHoverBg(0xFF, 0x18, 0x18, 0x18); // #181818 Secondary button hover
    static const Gdiplus::Color CtaHoverBg(0xFF, 0xE5, 0xE5, 0xE5);     // #E5E5E5 Primary CTA hover
}

struct AppState {
    UiLang ui_lang = UiLang::ID;
    PatchMode patch_mode = PatchMode::ID_HYBRID;
    std::wstring game_dir;
    std::vector<std::wstring> log_lines;
    std::wstring status_text = L"SIAP";
    Gdiplus::Color status_color = Theme::AccentGreen;
    bool is_busy = false;
    int hovered_btn = -1;
    std::mutex mtx;

    // Window dimensions (Fixed single-page 980 x 620)
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
    }
}

void SaveConfig() {
    std::wstring cfg_path = GetCeleslibAppDataDir() + L"\\config.json";
    std::ofstream f(cfg_path.c_str());
    if (!f.is_open()) return;
    f << "{\n";
    f << "  \"ui_lang\": \"" << (g_state.ui_lang == UiLang::EN ? "en" : "id") << "\",\n";
    f << "  \"patch_mode\": \"" << (g_state.patch_mode == PatchMode::EN_FULL ? "en" : "id") << "\"\n";
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
    g_state.status_color = Theme::AccentYellow;
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
                    g_state.status_color = Theme::AccentGreen;
                } else if (action == L"install" || res.state == L"installed") {
                    g_state.status_text = s.status_installed;
                    g_state.status_color = Theme::AccentGreen;
                } else {
                    g_state.status_text = s.status_ready;
                    g_state.status_color = Theme::AccentGreen;
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
    g_state.status_color = Theme::AccentYellow;
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

        AppendLog(L"[ANDROID] Menjalankan Android USB: " + cmd.str());

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
                g_state.status_color = Theme::AccentGreen;
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

// Crisp Vector Stroke Icons (2px stroke, clean geometric shapes)
void DrawCeleslibStar(Gdiplus::Graphics& g, float cx, float cy, float r, const Gdiplus::Brush& brush) {
    using namespace Gdiplus;
    PointF pts[8];
    float r_in = r * 0.32f;
    pts[0] = PointF(cx, cy - r);
    pts[1] = PointF(cx + r_in, cy - r_in);
    pts[2] = PointF(cx + r, cy);
    pts[3] = PointF(cx + r_in, cy + r_in);
    pts[4] = PointF(cx, cy + r);
    pts[5] = PointF(cx - r_in, cy + r_in);
    pts[6] = PointF(cx - r, cy);
    pts[7] = PointF(cx - r_in, cy - r_in);
    g.FillPolygon(&brush, pts, 8);
}

void DrawVectorFolder(Gdiplus::Graphics& g, float x, float y, const Gdiplus::Pen& pen) {
    // Folder icon 14x12
    g.DrawRectangle(&pen, x, y + 3, 14.0f, 9.0f);
    g.DrawLine(&pen, x, y + 3, x + 4, y);
    g.DrawLine(&pen, x + 4, y, x + 8, y);
    g.DrawLine(&pen, x + 8, y, x + 10, y + 3);
}

void DrawVectorLayers(Gdiplus::Graphics& g, float x, float y, const Gdiplus::Pen& pen) {
    // Layers icon 14x14
    Gdiplus::PointF p1[] = { Gdiplus::PointF(x + 7, y), Gdiplus::PointF(x + 14, y + 4), Gdiplus::PointF(x + 7, y + 8), Gdiplus::PointF(x, y + 4) };
    g.DrawPolygon(&pen, p1, 4);
    g.DrawLine(&pen, x + 1, y + 7, x + 7, y + 10);
    g.DrawLine(&pen, x + 7, y + 10, x + 13, y + 7);
    g.DrawLine(&pen, x + 1, y + 10, x + 7, y + 13);
    g.DrawLine(&pen, x + 7, y + 13, x + 13, y + 10);
}

void DrawVectorGlobe(Gdiplus::Graphics& g, float x, float y, const Gdiplus::Pen& pen) {
    // Globe icon circle with meridian & equator
    g.DrawEllipse(&pen, x, y, 13.0f, 13.0f);
    g.DrawEllipse(&pen, x + 3.5f, y, 6.0f, 13.0f);
    g.DrawLine(&pen, x, y + 6.5f, x + 13, y + 6.5f);
}

void DrawVectorPlay(Gdiplus::Graphics& g, float x, float y, const Gdiplus::Brush& brush) {
    // Triangle Play icon 10x12
    Gdiplus::PointF pts[] = { Gdiplus::PointF(x, y), Gdiplus::PointF(x + 10, y + 6), Gdiplus::PointF(x, y + 12) };
    g.FillPolygon(&brush, pts, 3);
}

void DrawVectorRotateCCW(Gdiplus::Graphics& g, float x, float y, const Gdiplus::Pen& pen) {
    // Rotate counter-clockwise arc + arrow
    g.DrawArc(&pen, x, y, 12.0f, 12.0f, 45, 270);
    g.DrawLine(&pen, x + 6, y, x + 2, y);
    g.DrawLine(&pen, x + 2, y, x + 2, y + 4);
}

void DrawVectorCheck(Gdiplus::Graphics& g, float x, float y, const Gdiplus::Pen& pen) {
    // Checkmark
    g.DrawLine(&pen, x, y + 6, x + 4, y + 10);
    g.DrawLine(&pen, x + 4, y + 10, x + 11, y + 1);
}

void DrawVectorSmartphone(Gdiplus::Graphics& g, float x, float y, const Gdiplus::Pen& pen) {
    // Phone outline + home button dot
    DrawRoundRect(g, pen, x, y, 10.0f, 14.0f, 2.0f);
    g.DrawLine(&pen, x + 4, y + 12, x + 6, y + 12);
}

void DrawVectorBolt(Gdiplus::Graphics& g, float x, float y, const Gdiplus::Brush& brush) {
    // Lightning bolt polygon
    Gdiplus::PointF pts[] = {
        Gdiplus::PointF(x + 6, y),
        Gdiplus::PointF(x, y + 7),
        Gdiplus::PointF(x + 5, y + 7),
        Gdiplus::PointF(x + 3, y + 14),
        Gdiplus::PointF(x + 10, y + 5),
        Gdiplus::PointF(x + 5, y + 5)
    };
    g.FillPolygon(&brush, pts, 6);
}

void DrawVectorTrash(Gdiplus::Graphics& g, float x, float y, const Gdiplus::Pen& pen) {
    // Trash bin icon
    g.DrawLine(&pen, x, y + 3, x + 12, y + 3);
    g.DrawLine(&pen, x + 4, y + 1, x + 8, y + 1);
    g.DrawLine(&pen, x + 2, y + 3, x + 3, y + 12);
    g.DrawLine(&pen, x + 3, y + 12, x + 9, y + 12);
    g.DrawLine(&pen, x + 9, y + 12, x + 10, y + 3);
    g.DrawLine(&pen, x + 5, y + 5, x + 5, y + 10);
    g.DrawLine(&pen, x + 7, y + 5, x + 7, y + 10);
}

// Master GDI+ Celeslib Frame Renderer (Single-Page Monochrome Obsidian UI)
void RenderCeleslibFrame(Gdiplus::Graphics& g, int width, int height, const AppState& state) {
    using namespace Gdiplus;
    g.SetSmoothingMode(SmoothingModeAntiAlias);
    g.SetTextRenderingHint(TextRenderingHintClearTypeGridFit);

    const Strings& s = GetStrings(state.ui_lang);

    // 0. Base Canvas Fill (#090909)
    SolidBrush bgCanvasBrush(Theme::BgCanvas);
    g.FillRectangle(&bgCanvasBrush, 0, 0, width, height);

    Pen borderDarkPen(Theme::BorderDark, 1.0f);
    Pen borderSubtlePen(Theme::BorderSubtle, 1.0f);
    Pen borderFaintPen(Theme::BorderFaint, 1.0f);
    Pen borderHoverPen(Theme::BorderHover, 1.0f);
    Pen borderRedPen(Theme::AccentRed, 1.0f);
    Pen iconWhitePen(Theme::TextWhite, 1.6f);
    Pen iconMutedPen(Theme::TextMuted, 1.4f);

    SolidBrush whiteBrush(Theme::PrimaryWhite);
    SolidBrush blackBrush(Theme::PrimaryBlack);
    SolidBrush textWhiteBrush(Theme::TextWhite);
    SolidBrush textLightBrush(Theme::TextLight);
    SolidBrush textSilverBrush(Theme::TextSilver);
    SolidBrush textMutedBrush(Theme::TextMuted);
    SolidBrush textSubtleBrush(Theme::TextSubtle);
    SolidBrush textFaintBrush(Theme::TextFaint);
    SolidBrush cardSurfaceBrush(Theme::CardSurface);
    SolidBrush inputSurfaceBrush(Theme::InputSurface);
    SolidBrush secHoverBrush(Theme::SecondaryHoverBg);
    SolidBrush ctaHoverBrush(Theme::CtaHoverBg);

    // Fonts
    FontFamily sansFamily(L"Segoe UI");
    Font fontTitle(&sansFamily, 11, FontStyleBold, UnitPoint);
    Font fontHeader(&sansFamily, 8.5f, FontStyleBold, UnitPoint);
    Font fontRegular(&sansFamily, 8.5f, FontStyleRegular, UnitPoint);
    Font fontSmall(&sansFamily, 8.0f, FontStyleRegular, UnitPoint);
    Font fontBadge(&sansFamily, 8.0f, FontStyleBold, UnitPoint);
    Font fontMono(L"Consolas", 8.5f, FontStyleRegular, UnitPoint);
    Font fontMonoBold(L"Consolas", 8.5f, FontStyleBold, UnitPoint);
    Font fontMonoLog(L"Consolas", 9.5f, FontStyleRegular, UnitPoint);

    // =========================================================================
    // ZONE 1: Custom Frameless Titlebar (Y: 0..38, X: 0..980)
    // =========================================================================
    g.DrawLine(&borderDarkPen, 0, 38, width, 38);

    // 4-Point Geometric Celeslib Star Logo
    DrawCeleslibStar(g, 27.0f, 19.0f, 7.5f, whiteBrush);

    // Brand Title: "Celeslib"
    g.DrawString(s.app_name, -1, &fontTitle, PointF(40.0f, 8.0f), &textWhiteBrush);

    // Version Pill: [ v1.0.0 ]
    SolidBrush verPillBg(Color(0xFF, 0x14, 0x14, 0x14));
    FillRoundRect(g, verPillBg, 114.0f, 10.0f, 52.0f, 18.0f, 3.0f);
    DrawRoundRect(g, borderDarkPen, 114.0f, 10.0f, 52.0f, 18.0f, 3.0f);
    g.DrawString(s.version_badge, -1, &fontBadge, PointF(120.0f, 11.5f), &textSilverBrush);

    // Titlebar Subtitle: "Honor of Kings: Ace Patcher • Game Build 1.4.12"
    g.DrawString(s.header_subtitle, -1, &fontRegular, PointF(176.0f, 11.0f), &textMutedBrush);

    // Window Controls: [—] [□] [×]
    // Minimize (ID: 101)
    if (state.hovered_btn == 101) {
        g.FillRectangle(&secHoverBrush, 842, 0, 46, 38);
    }
    g.DrawString(L"—", -1, &fontRegular, PointF(858.0f, 9.0f), &textSilverBrush);

    // Maximize/Restore (ID: 102)
    if (state.hovered_btn == 102) {
        g.FillRectangle(&secHoverBrush, 888, 0, 46, 38);
    }
    g.DrawString(L"□", -1, &fontRegular, PointF(904.0f, 9.0f), &textSilverBrush);

    // Close (ID: 103)
    if (state.hovered_btn == 103) {
        SolidBrush closeRedBrush(Theme::CloseHoverBg);
        g.FillRectangle(&closeRedBrush, 934, 0, 46, 38);
    }
    g.DrawString(L"×", -1, &fontRegular, PointF(950.0f, 9.0f), (state.hovered_btn == 103) ? &textWhiteBrush : &textSilverBrush);

    // =========================================================================
    // ZONE 2: Connected 3-Column Configuration Strip (Y: 50..146, X: 20..960)
    // =========================================================================
    FillRoundRect(g, cardSurfaceBrush, 20.0f, 50.0f, 940.0f, 96.0f, 10.0f);
    DrawRoundRect(g, borderDarkPen, 20.0f, 50.0f, 940.0f, 96.0f, 10.0f);

    // Vertical column dividers at X = 420 and X = 710
    g.DrawLine(&borderSubtlePen, 420, 62, 420, 134);
    g.DrawLine(&borderSubtlePen, 710, 62, 710, 134);

    // --- COLUMN 1: Game Directory (X: 20..420) ---
    DrawVectorFolder(g, 36.0f, 62.0f, iconMutedPen);
    g.DrawString(s.lbl_game_dir, -1, &fontHeader, PointF(56.0f, 61.0f), &textMutedBrush);

    // Mini Button [Auto-Detect] (ID: 201)
    bool auto_hover = (state.hovered_btn == 201);
    SolidBrush autoBg(auto_hover ? Theme::SecondaryHoverBg : Theme::BgCanvas);
    FillRoundRect(g, autoBg, 318.0f, 56.0f, 88.0f, 22.0f, 4.0f);
    DrawRoundRect(g, auto_hover ? borderHoverPen : borderDarkPen, 318.0f, 56.0f, 88.0f, 22.0f, 4.0f);
    g.DrawString(s.btn_autodetect, -1, &fontBadge, PointF(326.0f, 60.0f), &textSilverBrush);

    // Path Box (X: 34..312, Y: 86..120)
    FillRoundRect(g, inputSurfaceBrush, 34.0f, 86.0f, 278.0f, 34.0f, 6.0f);
    DrawRoundRect(g, borderSubtlePen, 34.0f, 86.0f, 278.0f, 34.0f, 6.0f);
    std::wstring display_path = state.game_dir.empty() ? L"C:\\Program Files\\WXQLauncher\\WXQ" : state.game_dir;
    g.DrawString(display_path.c_str(), -1, &fontMono, PointF(44.0f, 95.0f), &textLightBrush);

    // [Pilih Folder / Browse] Button (ID: 202)
    bool browse_hover = (state.hovered_btn == 202);
    SolidBrush browseBg(browse_hover ? Color(0xFF, 0x22, 0x22, 0x22) : Color(0xFF, 0x14, 0x14, 0x14));
    FillRoundRect(g, browseBg, 318.0f, 86.0f, 88.0f, 34.0f, 6.0f);
    DrawRoundRect(g, browse_hover ? borderHoverPen : borderDarkPen, 318.0f, 86.0f, 88.0f, 34.0f, 6.0f);
    g.DrawString(s.btn_browse, -1, &fontHeader, PointF(326.0f, 95.0f), &textWhiteBrush);

    // --- COLUMN 2: Game Patch Mode (X: 420..710) ---
    DrawVectorLayers(g, 436.0f, 62.0f, iconMutedPen);
    g.DrawString(s.lbl_patch_mode, -1, &fontHeader, PointF(456.0f, 61.0f), &textMutedBrush);

    // Segmented Control Pill (X: 434..696, Y: 86..120)
    FillRoundRect(g, inputSurfaceBrush, 434.0f, 86.0f, 262.0f, 34.0f, 6.0f);
    DrawRoundRect(g, borderDarkPen, 434.0f, 86.0f, 262.0f, 34.0f, 6.0f);

    // [ID Hybrid] Segment (ID: 203)
    bool id_mode_active = (state.patch_mode == PatchMode::ID_HYBRID);
    if (id_mode_active) {
        FillRoundRect(g, whiteBrush, 437.0f, 89.0f, 127.0f, 28.0f, 4.0f);
        g.DrawString(s.seg_mode_id, -1, &fontHeader, PointF(472.0f, 95.0f), &blackBrush);
    } else {
        if (state.hovered_btn == 203) {
            FillRoundRect(g, secHoverBrush, 437.0f, 89.0f, 127.0f, 28.0f, 4.0f);
        }
        g.DrawString(s.seg_mode_id, -1, &fontHeader, PointF(472.0f, 95.0f), &textMutedBrush);
    }

    // [EN Full] Segment (ID: 204)
    bool en_mode_active = (state.patch_mode == PatchMode::EN_FULL);
    if (en_mode_active) {
        FillRoundRect(g, whiteBrush, 566.0f, 89.0f, 127.0f, 28.0f, 4.0f);
        g.DrawString(s.seg_mode_en, -1, &fontHeader, PointF(606.0f, 95.0f), &blackBrush);
    } else {
        if (state.hovered_btn == 204) {
            FillRoundRect(g, secHoverBrush, 566.0f, 89.0f, 127.0f, 28.0f, 4.0f);
        }
        g.DrawString(s.seg_mode_en, -1, &fontHeader, PointF(606.0f, 95.0f), &textMutedBrush);
    }

    // Subtitle
    const wchar_t* mode_sub = (state.patch_mode == PatchMode::EN_FULL) ? s.desc_mode_en : s.desc_mode_id;
    g.DrawString(mode_sub, -1, &fontSmall, PointF(436.0f, 126.0f), &textSubtleBrush);

    // --- COLUMN 3: Interface Language (X: 710..960) ---
    DrawVectorGlobe(g, 726.0f, 62.0f, iconMutedPen);
    g.DrawString(s.lbl_ui_lang, -1, &fontHeader, PointF(746.0f, 61.0f), &textMutedBrush);

    // Segmented Control Pill (X: 724..946, Y: 86..120)
    FillRoundRect(g, inputSurfaceBrush, 724.0f, 86.0f, 222.0f, 34.0f, 6.0f);
    DrawRoundRect(g, borderDarkPen, 724.0f, 86.0f, 222.0f, 34.0f, 6.0f);

    // [Indonesia] Segment (ID: 205)
    bool id_ui_active = (state.ui_lang == UiLang::ID);
    if (id_ui_active) {
        FillRoundRect(g, whiteBrush, 727.0f, 89.0f, 107.0f, 28.0f, 4.0f);
        g.DrawString(s.seg_ui_id, -1, &fontHeader, PointF(752.0f, 95.0f), &blackBrush);
    } else {
        if (state.hovered_btn == 205) {
            FillRoundRect(g, secHoverBrush, 727.0f, 89.0f, 107.0f, 28.0f, 4.0f);
        }
        g.DrawString(s.seg_ui_id, -1, &fontHeader, PointF(752.0f, 95.0f), &textMutedBrush);
    }

    // [English] Segment (ID: 206)
    bool en_ui_active = (state.ui_lang == UiLang::EN);
    if (en_ui_active) {
        FillRoundRect(g, whiteBrush, 836.0f, 89.0f, 107.0f, 28.0f, 4.0f);
        g.DrawString(s.seg_ui_en, -1, &fontHeader, PointF(868.0f, 95.0f), &blackBrush);
    } else {
        if (state.hovered_btn == 206) {
            FillRoundRect(g, secHoverBrush, 836.0f, 89.0f, 107.0f, 28.0f, 4.0f);
        }
        g.DrawString(s.seg_ui_en, -1, &fontHeader, PointF(868.0f, 95.0f), &textMutedBrush);
    }

    // Subtitle
    g.DrawString(s.desc_ui, -1, &fontSmall, PointF(726.0f, 126.0f), &textSubtleBrush);

    // =========================================================================
    // ZONE 3: Unified Action Toolbar (Y: 158..208, X: 20..960)
    // =========================================================================
    FillRoundRect(g, cardSurfaceBrush, 20.0f, 158.0f, 940.0f, 50.0f, 8.0f);
    DrawRoundRect(g, borderDarkPen, 20.0f, 158.0f, 940.0f, 50.0f, 8.0f);

    // 1. Primary CTA: [▶ Pasang Patch] (ID: 301, X: 30..186, Y: 166..200)
    bool install_hover = (state.hovered_btn == 301);
    FillRoundRect(g, install_hover ? ctaHoverBrush : whiteBrush, 30.0f, 166.0f, 156.0f, 34.0f, 6.0f);
    DrawVectorPlay(g, 46.0f, 177.0f, blackBrush);
    g.DrawString(s.btn_install, -1, &fontHeader, PointF(64.0f, 175.0f), &blackBrush);

    // 2. [↺ Pulihkan] (ID: 302, X: 194..326, Y: 166..200)
    bool restore_hover = (state.hovered_btn == 302);
    SolidBrush restBg(restore_hover ? Theme::SecondaryHoverBg : Theme::BgCanvas);
    FillRoundRect(g, restBg, 194.0f, 166.0f, 132.0f, 34.0f, 6.0f);
    DrawRoundRect(g, restore_hover ? borderRedPen : borderDarkPen, 194.0f, 166.0f, 132.0f, 34.0f, 6.0f);
    Pen restPen(restore_hover ? Theme::AccentRed : Theme::TextWhite, 1.4f);
    DrawVectorRotateCCW(g, 208.0f, 177.0f, restPen);
    g.DrawString(s.btn_restore, -1, &fontHeader, PointF(228.0f, 175.0f), restore_hover ? (SolidBrush*)&borderRedPen : &textWhiteBrush);

    // 3. [✓ Periksa] (ID: 303, X: 334..462, Y: 166..200)
    bool verify_hover = (state.hovered_btn == 303);
    SolidBrush verBg(verify_hover ? Theme::SecondaryHoverBg : Theme::BgCanvas);
    FillRoundRect(g, verBg, 334.0f, 166.0f, 128.0f, 34.0f, 6.0f);
    DrawRoundRect(g, verify_hover ? borderHoverPen : borderDarkPen, 334.0f, 166.0f, 128.0f, 34.0f, 6.0f);
    DrawVectorCheck(g, 348.0f, 178.0f, iconWhitePen);
    g.DrawString(s.btn_verify, -1, &fontHeader, PointF(368.0f, 175.0f), &textWhiteBrush);

    // Vertical Divider at X = 476
    g.DrawLine(&borderSubtlePen, 476, 168, 476, 198);

    // 4. Android USB Actions:
    // [📱 Pindai USB] (ID: 304, X: 490..616, Y: 166..200)
    bool scan_hover = (state.hovered_btn == 304);
    SolidBrush scanBg(scan_hover ? Theme::SecondaryHoverBg : Theme::BgCanvas);
    FillRoundRect(g, scanBg, 490.0f, 166.0f, 126.0f, 34.0f, 6.0f);
    DrawRoundRect(g, scan_hover ? borderHoverPen : borderDarkPen, 490.0f, 166.0f, 126.0f, 34.0f, 6.0f);
    DrawVectorSmartphone(g, 502.0f, 176.0f, iconWhitePen);
    g.DrawString(s.btn_android_scan, -1, &fontHeader, PointF(520.0f, 175.0f), &textWhiteBrush);

    // [⚡ Patch APK] (ID: 305, X: 624..740, Y: 166..200)
    bool patch_hover = (state.hovered_btn == 305);
    SolidBrush apkBg(patch_hover ? Theme::SecondaryHoverBg : Theme::BgCanvas);
    FillRoundRect(g, apkBg, 624.0f, 166.0f, 116.0f, 34.0f, 6.0f);
    DrawRoundRect(g, patch_hover ? borderHoverPen : borderDarkPen, 624.0f, 166.0f, 116.0f, 34.0f, 6.0f);
    DrawVectorBolt(g, 636.0f, 176.0f, whiteBrush);
    g.DrawString(s.btn_android_patch, -1, &fontHeader, PointF(654.0f, 175.0f), &textWhiteBrush);

    // [↺ Pulihkan APK] (ID: 306, X: 748..868, Y: 166..200)
    bool rec_hover = (state.hovered_btn == 306);
    SolidBrush recBg(rec_hover ? Theme::SecondaryHoverBg : Theme::BgCanvas);
    FillRoundRect(g, recBg, 748.0f, 166.0f, 120.0f, 34.0f, 6.0f);
    DrawRoundRect(g, rec_hover ? borderRedPen : borderDarkPen, 748.0f, 166.0f, 120.0f, 34.0f, 6.0f);
    Pen recPen(rec_hover ? Theme::AccentRed : Theme::TextWhite, 1.4f);
    DrawVectorRotateCCW(g, 758.0f, 177.0f, recPen);
    g.DrawString(s.btn_android_recover, -1, &fontHeader, PointF(776.0f, 175.0f), rec_hover ? (SolidBrush*)&borderRedPen : &textWhiteBrush);

    // 5. Console [🗑 Clear] (ID: 307, X: 878..950, Y: 166..200)
    bool clear_hover = (state.hovered_btn == 307);
    SolidBrush clrBg(clear_hover ? Theme::SecondaryHoverBg : Theme::BgCanvas);
    FillRoundRect(g, clrBg, 878.0f, 166.0f, 72.0f, 34.0f, 6.0f);
    DrawRoundRect(g, clear_hover ? borderHoverPen : borderDarkPen, 878.0f, 166.0f, 72.0f, 34.0f, 6.0f);
    DrawVectorTrash(g, 888.0f, 176.0f, iconWhitePen);
    g.DrawString(s.btn_clear, -1, &fontHeader, PointF(906.0f, 175.0f), &textWhiteBrush);

    // =========================================================================
    // ZONE 4: Diagnostic Console (Y: 220..576, X: 20..960)
    // =========================================================================
    FillRoundRect(g, inputSurfaceBrush, 20.0f, 220.0f, 940.0f, 356.0f, 8.0f);
    DrawRoundRect(g, borderDarkPen, 20.0f, 220.0f, 940.0f, 356.0f, 8.0f);

    // Console Header Bar (Y: 220..252)
    FillRoundRect(g, cardSurfaceBrush, 20.0f, 220.0f, 940.0f, 32.0f, 8.0f);
    g.FillRectangle(&cardSurfaceBrush, 20, 240, 940, 12);
    g.DrawLine(&borderSubtlePen, 20, 252, 960, 252);

    // Header label: Terminal prompt ">_" + title
    g.DrawString(L">_", -1, &fontMonoBold, PointF(34.0f, 228.0f), &textWhiteBrush);
    g.DrawString(s.console_title, -1, &fontMono, PointF(56.0f, 228.0f), &textSilverBrush);

    // Status Pill (X: 830..948, Y: 224..248)
    SolidBrush statusPillBg(Theme::CardSurfaceElevated);
    FillRoundRect(g, statusPillBg, 830.0f, 224.0f, 118.0f, 24.0f, 4.0f);
    DrawRoundRect(g, borderDarkPen, 830.0f, 224.0f, 118.0f, 24.0f, 4.0f);

    // Glowing dot 8x8
    SolidBrush dotBrush(state.status_color);
    g.FillEllipse(&dotBrush, 840, 232, 8, 8);
    g.DrawString(state.status_text.c_str(), -1, &fontMonoBold, PointF(854.0f, 228.0f), &textWhiteBrush);

    // Line Number Gutter (X: 21..64, Y: 253..575)
    SolidBrush gutterBg(Theme::BgCanvas);
    g.FillRectangle(&gutterBg, 21, 253, 43, 322);
    g.DrawLine(&borderFaintPen, 64, 253, 64, 575);

    // Minimap Rail (X: 908..959, Y: 253..575)
    g.FillRectangle(&gutterBg, 908, 253, 51, 322);
    g.DrawLine(&borderFaintPen, 908, 253, 908, 575);

    // Render Log Lines in Viewport
    if (state.log_lines.empty()) {
        g.DrawString(L"001", -1, &fontMono, PointF(32.0f, 260.0f), &textFaintBrush);
        g.DrawString(s.console_placeholder, -1, &fontMonoLog, PointF(76.0f, 260.0f), &textMutedBrush);
    } else {
        int max_visible = 16;
        int start_idx = (int)state.log_lines.size() > max_visible ? (int)state.log_lines.size() - max_visible : 0;
        int line_y = 260;
        for (size_t i = start_idx; i < state.log_lines.size(); ++i) {
            wchar_t num_str[16];
            swprintf_s(num_str, L"%03d", (int)i + 1);
            g.DrawString(num_str, -1, &fontMono, PointF(32.0f, (float)line_y), &textFaintBrush);

            const std::wstring& line = state.log_lines[i];
            Color lineCol(0xFF, 0xB0, 0xB0, 0xB0);
            if (line.find(L"[OK]") != std::wstring::npos || line.find(L"[READY]") != std::wstring::npos) {
                lineCol = Theme::AccentGreen;
            } else if (line.find(L"[ERROR]") != std::wstring::npos || line.find(L"[FAIL]") != std::wstring::npos) {
                lineCol = Theme::AccentRed;
            } else if (line.find(L"[PATCH]") != std::wstring::npos || line.find(L"[CHECK]") != std::wstring::npos || line.find(L"[ANDROID]") != std::wstring::npos) {
                lineCol = Theme::TextWhite;
            }

            SolidBrush lineBrush(lineCol);
            g.DrawString(line.c_str(), -1, &fontMonoLog, PointF(76.0f, (float)line_y), &lineBrush);

            // Minimap micro-bar
            Pen miniPen(lineCol, 1.0f);
            g.DrawLine(&miniPen, 916, line_y + 6, 950, line_y + 6);

            line_y += 19;
        }
    }

    // =========================================================================
    // ZONE 5: Bottom Status Bar (Y: 588..620, X: 0..980)
    // =========================================================================
    g.DrawLine(&borderDarkPen, 0, 588, width, 588);

    // Left Engine Status Info + Glowing Green Dot
    SolidBrush greenDotBrush(Theme::AccentGreen);
    g.FillEllipse(&greenDotBrush, 22, 600, 8, 8);
    g.DrawString(s.bottom_engine_info, -1, &fontRegular, PointF(38.0f, 597.0f), &textSilverBrush);

    // Right Copyright
    g.DrawString(s.bottom_copyright, -1, &fontRegular, PointF(712.0f, 597.0f), &textMutedBrush);
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

            // Zone 1: Window Controls
            if (y >= 0 && y <= 38) {
                if (x >= 842 && x <= 888) new_hover = 101;
                else if (x >= 888 && x <= 934) new_hover = 102;
                else if (x >= 934 && x <= 980) new_hover = 103;
            }
            // Zone 2: Configuration Strip
            else if (y >= 50 && y <= 146) {
                if (y >= 56 && y <= 78 && x >= 318 && x <= 406) new_hover = 201; // Auto-Detect
                else if (y >= 86 && y <= 120 && x >= 318 && x <= 406) new_hover = 202; // Browse
                else if (y >= 89 && y <= 117 && x >= 437 && x <= 564) new_hover = 203; // ID Hybrid
                else if (y >= 89 && y <= 117 && x >= 566 && x <= 693) new_hover = 204; // EN Full
                else if (y >= 89 && y <= 117 && x >= 727 && x <= 834) new_hover = 205; // ID Lang
                else if (y >= 89 && y <= 117 && x >= 836 && x <= 943) new_hover = 206; // EN Lang
            }
            // Zone 3: Action Toolbar
            else if (y >= 166 && y <= 200) {
                if (x >= 30 && x <= 186) new_hover = 301;      // Install
                else if (x >= 194 && x <= 326) new_hover = 302; // Restore
                else if (x >= 334 && x <= 462) new_hover = 303; // Verify
                else if (x >= 490 && x <= 616) new_hover = 304; // Android Scan
                else if (x >= 624 && x <= 740) new_hover = 305; // Android Patch
                else if (x >= 748 && x <= 868) new_hover = 306; // Android Recover
                else if (x >= 878 && x <= 950) new_hover = 307; // Clear
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

            // Zone 1: Window Controls & Dragging
            if (y >= 0 && y <= 38) {
                if (x >= 842 && x <= 888) {
                    ShowWindow(hwnd, SW_MINIMIZE);
                    return 0;
                }
                if (x >= 888 && x <= 934) {
                    WINDOWPLACEMENT wp = { sizeof(wp) };
                    GetWindowPlacement(hwnd, &wp);
                    if (wp.showCmd == SW_MAXIMIZE) {
                        ShowWindow(hwnd, SW_RESTORE);
                    } else {
                        ShowWindow(hwnd, SW_MAXIMIZE);
                    }
                    return 0;
                }
                if (x >= 934 && x <= 980) {
                    PostQuitMessage(0);
                    return 0;
                }
                // Drag window on titlebar
                if (x < 842) {
                    ReleaseCapture();
                    SendMessageW(hwnd, WM_NCLBUTTONDOWN, HTCAPTION, 0);
                    return 0;
                }
            }

            // Zone 2: Configuration Strip
            if (y >= 50 && y <= 146) {
                // Auto-Detect (ID: 201)
                if (y >= 56 && y <= 78 && x >= 318 && x <= 406) {
                    ExecuteWorkerAction(L"discover", L"");
                    return 0;
                }
                // Browse Folder (ID: 202)
                if (y >= 86 && y <= 120 && x >= 318 && x <= 406) {
                    const Strings& s = GetStrings(g_state.ui_lang);
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
                // Patch Mode: ID Hybrid (ID: 203)
                if (y >= 89 && y <= 117 && x >= 437 && x <= 564) {
                    g_state.patch_mode = PatchMode::ID_HYBRID;
                    SaveConfig();
                    InvalidateRect(hwnd, NULL, FALSE);
                    return 0;
                }
                // Patch Mode: EN Full (ID: 204)
                if (y >= 89 && y <= 117 && x >= 566 && x <= 693) {
                    g_state.patch_mode = PatchMode::EN_FULL;
                    SaveConfig();
                    InvalidateRect(hwnd, NULL, FALSE);
                    return 0;
                }
                // UI Language: Indonesia (ID: 205)
                if (y >= 89 && y <= 117 && x >= 727 && x <= 834) {
                    g_state.ui_lang = UiLang::ID;
                    SaveConfig();
                    InvalidateRect(hwnd, NULL, FALSE);
                    return 0;
                }
                // UI Language: English (ID: 206)
                if (y >= 89 && y <= 117 && x >= 836 && x <= 943) {
                    g_state.ui_lang = UiLang::EN;
                    SaveConfig();
                    InvalidateRect(hwnd, NULL, FALSE);
                    return 0;
                }
            }

            // Zone 3: Unified Action Toolbar
            if (y >= 166 && y <= 200) {
                const Strings& s = GetStrings(g_state.ui_lang);

                // 1. Install Patch (ID: 301)
                if (x >= 30 && x <= 186) {
                    if (MessageBoxW(hwnd, s.confirm_install_msg, s.confirm_install_title, MB_YESNO | MB_ICONQUESTION) == IDYES) {
                        ExecuteWorkerAction(L"install", g_state.game_dir);
                    }
                    return 0;
                }
                // 2. Restore (ID: 302)
                if (x >= 194 && x <= 326) {
                    if (MessageBoxW(hwnd, s.confirm_restore_msg, s.confirm_restore_title, MB_YESNO | MB_ICONQUESTION) == IDYES) {
                        ExecuteWorkerAction(L"restore", g_state.game_dir);
                    }
                    return 0;
                }
                // 3. Verify / Check (ID: 303)
                if (x >= 334 && x <= 462) {
                    ExecuteWorkerAction(L"status", g_state.game_dir);
                    return 0;
                }
                // 4. Android Scan (ID: 304)
                if (x >= 490 && x <= 616) {
                    ExecuteMobileWorkerAction(L"devices");
                    return 0;
                }
                // 5. Android Patch (ID: 305)
                if (x >= 624 && x <= 740) {
                    ExecuteMobileWorkerAction(L"patch");
                    return 0;
                }
                // 6. Android Recover (ID: 306)
                if (x >= 748 && x <= 868) {
                    ExecuteMobileWorkerAction(L"recover");
                    return 0;
                }
                // 7. Clear Log (ID: 307)
                if (x >= 878 && x <= 950) {
                    std::lock_guard<std::mutex> lock(g_state.mtx);
                    g_state.log_lines.clear();
                    InvalidateRect(hwnd, NULL, FALSE);
                    return 0;
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

// Offscreen PNG Smoke UI Exporter (Single-Page)
int RenderOffscreenPreview(const std::wstring& out_png_path, UiLang ui_lang, PatchMode mode) {
    using namespace Gdiplus;
    int w = 980, h = 620;
    Bitmap bmp(w, h, PixelFormat32bppARGB);
    {
        Graphics g(&bmp);
        AppState state;
        state.ui_lang = ui_lang;
        state.patch_mode = mode;
        state.width = w;
        state.height = h;
        state.game_dir = L"C:\\Program Files\\WXQLauncher\\WXQ";
        state.status_text = (ui_lang == UiLang::EN) ? L"READY" : L"SIAP";
        state.status_color = Theme::AccentGreen;
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
            RenderOffscreenPreview(out_dir + L"\\celeslib_patcher_id.png", UiLang::ID, PatchMode::ID_HYBRID);
            RenderOffscreenPreview(out_dir + L"\\celeslib_patcher_en.png", UiLang::EN, PatchMode::EN_FULL);
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
        WS_POPUP | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU,
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
