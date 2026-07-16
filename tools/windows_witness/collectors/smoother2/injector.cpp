#include <windows.h>
#include <tlhelp32.h>
#include <cstdint>
#include <cstring>
#include <cwchar>
#include <iostream>
#include <string>
#include <vector>

namespace {
constexpr char kInitializeExport[] = "OLMInitializeCollector";
constexpr DWORD kInitializeAccepted = 1;
constexpr DWORD kRemoteTimeoutMs = 30000;

struct ExportInfo {
    uintptr_t rva = 0;
    DWORD image_size = 0;
};

bool module_export_info(HMODULE module, const char* export_name, ExportInfo& info) {
    if (!module) return false;
    FARPROC exported = GetProcAddress(module, export_name);
    auto* dos = reinterpret_cast<const IMAGE_DOS_HEADER*>(module);
    bool valid = exported && dos->e_magic == IMAGE_DOS_SIGNATURE;
    const IMAGE_NT_HEADERS64* nt = nullptr;
    if (valid) {
        nt = reinterpret_cast<const IMAGE_NT_HEADERS64*>(reinterpret_cast<const BYTE*>(module) + dos->e_lfanew);
        valid = nt->Signature == IMAGE_NT_SIGNATURE && nt->OptionalHeader.Magic == IMAGE_NT_OPTIONAL_HDR64_MAGIC;
    }
    if (valid) {
        uintptr_t base = reinterpret_cast<uintptr_t>(module);
        uintptr_t address = reinterpret_cast<uintptr_t>(exported);
        valid = address >= base;
        if (valid) {
            info.rva = address - base;
            info.image_size = nt->OptionalHeader.SizeOfImage;
            valid = info.rva < info.image_size;
        }
    }
    return valid;
}

bool absolute_path(const std::wstring& path) {
    return path.size() > 2 && ((path[0] >= L'A' && path[0] <= L'Z') || (path[0] >= L'a' && path[0] <= L'z')) &&
           path[1] == L':' && (path[2] == L'\\' || path[2] == L'/');
}

int usage() {
    std::wcerr << L"usage: olm_injector.exe --pid <PID> --dll <absolute DLL> --config <absolute JSON>\n";
    return 2;
}

bool canonical_existing_path(const std::wstring& path, std::wstring& canonical) {
    HANDLE file = CreateFileW(path.c_str(), FILE_READ_ATTRIBUTES,
                              FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                              nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) return false;
    DWORD needed = GetFinalPathNameByHandleW(file, nullptr, 0, FILE_NAME_NORMALIZED | VOLUME_NAME_DOS);
    if (!needed) { CloseHandle(file); return false; }
    std::vector<wchar_t> buffer(needed);
    DWORD length = GetFinalPathNameByHandleW(file, buffer.data(), needed, FILE_NAME_NORMALIZED | VOLUME_NAME_DOS);
    CloseHandle(file);
    if (!length || length >= needed) return false;
    canonical.assign(buffer.data(), length);
    if (canonical.rfind(L"\\\\?\\UNC\\", 0) == 0) canonical = L"\\\\" + canonical.substr(8);
    else if (canonical.rfind(L"\\\\?\\", 0) == 0) canonical.erase(0, 4);
    for (wchar_t& c : canonical) if (c == L'/') c = L'\\';
    return true;
}

std::wstring base_name(const std::wstring& path) {
    size_t separator = path.find_last_of(L"\\/");
    return separator == std::wstring::npos ? path : path.substr(separator + 1);
}

bool local_export_info(const std::wstring& dll, ExportInfo& info) {
    HMODULE module = LoadLibraryExW(dll.c_str(), nullptr, DONT_RESOLVE_DLL_REFERENCES);
    if (!module) { std::wcerr << L"LoadLibraryExW(DONT_RESOLVE_DLL_REFERENCES) failed: " << GetLastError() << L"\n"; return false; }
    bool valid = module_export_info(module, kInitializeExport, info);
    FreeLibrary(module);
    if (!valid) std::wcerr << L"collector export or PE identity is invalid\n";
    return valid;
}

bool remote_system_module_base(DWORD pid, const wchar_t* module_name, DWORD expected_size, uintptr_t& remote_base) {
    HANDLE snapshot = INVALID_HANDLE_VALUE;
    for (unsigned attempt = 0; attempt < 8; ++attempt) {
        snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid);
        if (snapshot != INVALID_HANDLE_VALUE || GetLastError() != ERROR_BAD_LENGTH) break;
        Sleep(10);
    }
    if (snapshot == INVALID_HANDLE_VALUE) {
        std::wcerr << L"CreateToolhelp32Snapshot for system module failed: " << GetLastError() << L"\n";
        return false;
    }
    unsigned matches = 0;
    MODULEENTRY32W entry{};
    entry.dwSize = sizeof(entry);
    if (Module32FirstW(snapshot, &entry)) {
        do {
            if (!_wcsicmp(entry.szModule, module_name) && entry.modBaseSize == expected_size) {
                ++matches;
                remote_base = reinterpret_cast<uintptr_t>(entry.modBaseAddr);
            }
        } while (Module32NextW(snapshot, &entry));
    }
    CloseHandle(snapshot);
    if (matches != 1) {
        std::wcerr << L"remote system module identity ambiguous: module=" << module_name
                   << L" matches=" << matches << L"\n";
        remote_base = 0;
        return false;
    }
    return true;
}

bool farproc_as_thread_start(FARPROC procedure, LPTHREAD_START_ROUTINE& start) {
    static_assert(sizeof(start) == sizeof(procedure), "function pointer size mismatch");
    if (!procedure) return false;
    memcpy(&start, &procedure, sizeof(start));
    return true;
}

bool address_as_thread_start(uintptr_t address, LPTHREAD_START_ROUTINE& start) {
    static_assert(sizeof(start) == sizeof(address), "function pointer size mismatch");
    if (!address) return false;
    memcpy(&start, &address, sizeof(start));
    return true;
}

bool remote_module_base(DWORD pid, const std::wstring& requested_dll, DWORD expected_size, uintptr_t& remote_base) {
    std::wstring requested_path;
    if (!canonical_existing_path(requested_dll, requested_path)) {
        std::wcerr << L"failed to normalize requested DLL path: " << GetLastError() << L"\n";
        return false;
    }
    std::wstring requested_name = base_name(requested_path);
    HANDLE snapshot = INVALID_HANDLE_VALUE;
    for (unsigned attempt = 0; attempt < 8; ++attempt) {
        snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid);
        if (snapshot != INVALID_HANDLE_VALUE || GetLastError() != ERROR_BAD_LENGTH) break;
        Sleep(10);
    }
    if (snapshot == INVALID_HANDLE_VALUE) {
        std::wcerr << L"CreateToolhelp32Snapshot failed: " << GetLastError() << L"\n";
        return false;
    }
    unsigned path_matches = 0, identity_matches = 0;
    MODULEENTRY32W entry{}; entry.dwSize = sizeof(entry);
    if (Module32FirstW(snapshot, &entry)) {
        do {
            std::wstring candidate_path;
            if (!canonical_existing_path(entry.szExePath, candidate_path)) continue;
            if (_wcsicmp(candidate_path.c_str(), requested_path.c_str()) || _wcsicmp(entry.szModule, requested_name.c_str())) continue;
            ++path_matches;
            if (entry.modBaseSize == expected_size) {
                ++identity_matches;
                remote_base = reinterpret_cast<uintptr_t>(entry.modBaseAddr);
            }
        } while (Module32NextW(snapshot, &entry));
    }
    DWORD enumeration_error = GetLastError();
    CloseHandle(snapshot);
    if (path_matches != 1 || identity_matches != 1) {
        std::wcerr << L"remote collector identity ambiguous: path_matches=" << path_matches
                   << L" image_matches=" << identity_matches << L" enumeration_error=" << enumeration_error << L"\n";
        remote_base = 0;
        return false;
    }
    return true;
}

bool write_remote_wstring(HANDLE process, const std::wstring& value, void*& remote) {
    SIZE_T bytes = (value.size() + 1) * sizeof(wchar_t);
    remote = VirtualAllocEx(process, nullptr, bytes, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!remote) return false;
    SIZE_T written = 0;
    if (!WriteProcessMemory(process, remote, value.c_str(), bytes, &written) || written != bytes) {
        VirtualFreeEx(process, remote, 0, MEM_RELEASE); remote = nullptr; return false;
    }
    return true;
}
}

int wmain(int argc, wchar_t** argv) {
    DWORD pid = 0;
    std::wstring dll, config;
    for (int i = 1; i < argc; ++i) {
        std::wstring argument = argv[i];
        if (argument == L"--pid" && i + 1 < argc) pid = wcstoul(argv[++i], nullptr, 10);
        else if (argument == L"--dll" && i + 1 < argc) dll = argv[++i];
        else if (argument == L"--config" && i + 1 < argc) config = argv[++i];
        else return usage();
    }
    if (!pid || !absolute_path(dll) || !absolute_path(config)) return usage();
    std::wstring resolved_config;
    if (!canonical_existing_path(config, resolved_config)) {
        std::wcerr << L"config path does not resolve to an existing file: " << GetLastError() << L"\n";
        return 1;
    }
    ExportInfo export_info;
    if (!local_export_info(dll, export_info)) return 1;

    HANDLE process = OpenProcess(PROCESS_CREATE_THREAD | PROCESS_QUERY_INFORMATION |
                                 PROCESS_VM_OPERATION | PROCESS_VM_WRITE | PROCESS_VM_READ,
                                 FALSE, pid);
    if (!process) { std::wcerr << L"OpenProcess failed: " << GetLastError() << L"\n"; return 1; }

    void* remote_dll = nullptr;
    if (!write_remote_wstring(process, dll, remote_dll)) {
        std::wcerr << L"remote DLL path setup failed: " << GetLastError() << L"\n";
        CloseHandle(process); return 1;
    }
    ExportInfo load_library_info;
    if (!module_export_info(GetModuleHandleW(L"kernel32.dll"), "LoadLibraryW", load_library_info)) {
        std::wcerr << L"local kernel32!LoadLibraryW identity is invalid\n";
        VirtualFreeEx(process, remote_dll, 0, MEM_RELEASE); CloseHandle(process); return 1;
    }
    uintptr_t remote_kernel32 = 0;
    if (!remote_system_module_base(pid, L"kernel32.dll", load_library_info.image_size, remote_kernel32) ||
        load_library_info.rva > UINTPTR_MAX - remote_kernel32) {
        VirtualFreeEx(process, remote_dll, 0, MEM_RELEASE); CloseHandle(process); return 1;
    }
    LPTHREAD_START_ROUTINE load_library = nullptr;
    if (!address_as_thread_start(remote_kernel32 + load_library_info.rva, load_library)) {
        std::wcerr << L"remote LoadLibraryW address is invalid\n";
        VirtualFreeEx(process, remote_dll, 0, MEM_RELEASE); CloseHandle(process); return 1;
    }
    HANDLE load_thread = CreateRemoteThread(process, nullptr, 0, load_library, remote_dll, 0, nullptr);
    if (!load_thread) {
        std::wcerr << L"CreateRemoteThread(LoadLibraryW) failed: " << GetLastError() << L"\n";
        VirtualFreeEx(process, remote_dll, 0, MEM_RELEASE); CloseHandle(process); return 1;
    }
    DWORD wait_result = WaitForSingleObject(load_thread, kRemoteTimeoutMs);
    if (wait_result != WAIT_OBJECT_0) {
        std::wcerr << (wait_result == WAIT_TIMEOUT ? L"LoadLibraryW thread timed out" : L"waiting for LoadLibraryW failed")
                   << L"; remote DLL path retained while thread state is uncertain\n";
        CloseHandle(load_thread); CloseHandle(process); return 1;
    }
    DWORD load_exit = 0;
    if (!GetExitCodeThread(load_thread, &load_exit)) {
        std::wcerr << L"GetExitCodeThread(LoadLibraryW) failed: " << GetLastError() << L"\n";
        VirtualFreeEx(process, remote_dll, 0, MEM_RELEASE); CloseHandle(load_thread); CloseHandle(process); return 1;
    }
    VirtualFreeEx(process, remote_dll, 0, MEM_RELEASE); CloseHandle(load_thread);

    uintptr_t remote_base = 0;
    if (!remote_module_base(pid, dll, export_info.image_size, remote_base)) { CloseHandle(process); return 1; }
    if (export_info.rva > UINTPTR_MAX - remote_base) {
        std::wcerr << L"remote initialization address overflow\n"; CloseHandle(process); return 1;
    }
    uintptr_t remote_initialize_address = remote_base + export_info.rva;
    LPTHREAD_START_ROUTINE remote_initialize = nullptr;
    if (!address_as_thread_start(remote_initialize_address, remote_initialize)) {
        std::wcerr << L"remote initialization address invalid\n"; CloseHandle(process); return 1;
    }

    void* remote_config = nullptr;
    if (!write_remote_wstring(process, config, remote_config)) {
        std::wcerr << L"remote config path setup failed: " << GetLastError() << L"\n";
        CloseHandle(process); return 1;
    }
    HANDLE initialize_thread = CreateRemoteThread(process, nullptr, 0, remote_initialize, remote_config, 0, nullptr);
    if (!initialize_thread) {
        std::wcerr << L"CreateRemoteThread(OLMInitializeCollector) failed: " << GetLastError() << L"\n";
        VirtualFreeEx(process, remote_config, 0, MEM_RELEASE); CloseHandle(process); return 1;
    }
    wait_result = WaitForSingleObject(initialize_thread, kRemoteTimeoutMs);
    if (wait_result != WAIT_OBJECT_0) {
        std::wcerr << (wait_result == WAIT_TIMEOUT ? L"OLMInitializeCollector timed out" : L"waiting for OLMInitializeCollector failed")
                   << L"; remote config path retained while thread state is uncertain\n";
        CloseHandle(initialize_thread); CloseHandle(process); return 1;
    }
    DWORD initialize_exit = 0;
    if (!GetExitCodeThread(initialize_thread, &initialize_exit)) {
        std::wcerr << L"GetExitCodeThread(OLMInitializeCollector) failed: " << GetLastError() << L"\n";
        VirtualFreeEx(process, remote_config, 0, MEM_RELEASE); CloseHandle(initialize_thread); CloseHandle(process); return 1;
    }
    VirtualFreeEx(process, remote_config, 0, MEM_RELEASE); CloseHandle(initialize_thread); CloseHandle(process);
    if (initialize_exit != kInitializeAccepted) {
        std::wcerr << L"OLMInitializeCollector rejected start: exit_code=" << initialize_exit << L"\n";
        return 1;
    }
    std::wcout << L"collector loaded and initialization accepted; remote_base=0x" << std::hex << remote_base
               << L" export_rva=0x" << export_info.rva << L" loadlibrary_exit=0x" << load_exit << L"\n";
    return 0;
}
