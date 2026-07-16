#include <windows.h>
#include <bcrypt.h>
#include <psapi.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cwchar>
#include <fstream>
#include <iterator>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <atomic>
#include <stdexcept>
#include <utility>

namespace {

constexpr char kWitnessId[] = "olmsmoother2-legacy-key-producer-common-core-v1";
constexpr DWORD kConfigPathCapacity = 32768;
constexpr DWORD kInitializeAccepted = 1;

struct Json {
    enum Kind { null_value, string_value, number_value, object_value, array_value, boolean_value } kind = null_value;
    std::string s;
    double n = 0;
    bool b = false;
    std::unordered_map<std::string, Json> o;
    std::vector<Json> a;
};

class JsonParser {
    const char* p_;
    const char* end_;
    void ws() { while (p_ < end_ && (*p_ == ' ' || *p_ == '\n' || *p_ == '\r' || *p_ == '\t')) ++p_; }
    bool take(char c) { ws(); if (p_ >= end_ || *p_ != c) return false; ++p_; return true; }
    bool string(std::string& out) {
        ws(); if (p_ >= end_ || *p_++ != '"') return false; out.clear();
        while (p_ < end_ && *p_ != '"') {
            if (*p_ == '\\') { ++p_; if (p_ >= end_) return false; char c = *p_++; out += c == 'n' ? '\n' : c == 'r' ? '\r' : c == 't' ? '\t' : c; }
            else out += *p_++;
        }
        return p_ < end_ && *p_++ == '"';
    }
    bool parse_value(Json& out) {
        ws(); if (p_ >= end_) return false;
        if (*p_ == '"') { out.kind = Json::string_value; return string(out.s); }
        if (*p_ == '{') return object(out);
        if (*p_ == '[') return array(out);
        if (end_ - p_ >= 4 && !strncmp(p_, "true", 4)) { p_ += 4; out.kind = Json::boolean_value; out.b = true; return true; }
        if (end_ - p_ >= 5 && !strncmp(p_, "false", 5)) { p_ += 5; out.kind = Json::boolean_value; out.b = false; return true; }
        char* finish = nullptr; out.n = strtod(p_, &finish); if (finish == p_) return false; p_ = finish; out.kind = Json::number_value; return true;
    }
    bool object(Json& out) {
        out.kind = Json::object_value; if (!take('{')) return false; ws(); if (take('}')) return true;
        for (;;) { std::string key; Json value; if (!string(key) || !take(':') || !value_from(value)) return false; if (!out.o.emplace(std::move(key), std::move(value)).second) return false; if (take('}')) return true; if (!take(',')) return false; }
    }
    bool array(Json& out) {
        out.kind = Json::array_value; if (!take('[')) return false; ws(); if (take(']')) return true;
        for (;;) { Json value; if (!value_from(value)) return false; out.a.emplace_back(std::move(value)); if (take(']')) return true; if (!take(',')) return false; }
    }
    bool value_from(Json& value) { return parse_value(value); }
public:
    JsonParser(const std::string& input) : p_(input.data()), end_(p_ + input.size()) {}
    bool parse(Json& out) { if (!value_from(out)) return false; ws(); return p_ == end_; }
};

struct Probe {
    enum Kind { anchor, c280_entry, cardinal_10760, d3b0_entry, da50_entry, fef0_entry, e170_entry, e170_return, f270_entry, f270_return, e3a0_entry, e3a0_return } kind;
    std::string name;
    uintptr_t rva = 0;
    uintptr_t return_rva = 0;
    bool returns = false;
};
struct Config {
    std::string run_id, case_id, module, sha256, renderer;
    DWORD ae_pid = 0;
    unsigned project_bpc = 0;
    unsigned target_x = 0, target_y = 0;
    DWORD timeout_ms = 30000;
    std::wstring output_dir;
    std::vector<Probe> probes;
};
struct Installed { uintptr_t address; BYTE original; Probe::Kind kind; bool returns; };

std::string lower(std::string value) { for (char& c : value) if (c >= 'A' && c <= 'Z') c = char(c + ('a' - 'A')); return value; }
std::string escape_json(const std::string& value) { std::string out; for (char c : value) { if (c == '"' || c == '\\') out += '\\'; if (c == '\n') { out += "\\n"; continue; } out += c; } return out; }
std::string utf8(const std::wstring& value) { int n = WideCharToMultiByte(CP_UTF8, 0, value.data(), (int)value.size(), nullptr, 0, nullptr, nullptr); std::string out(n, '\0'); if (n) WideCharToMultiByte(CP_UTF8, 0, value.data(), (int)value.size(), out.data(), n, nullptr, nullptr); return out; }
bool read_file(const std::wstring& path, std::string& out) {
    std::ifstream file(path, std::ios::binary);
    if (!file) return false;
    out.assign((std::istreambuf_iterator<char>(file)), {});
    if (out.size() >= 3 && static_cast<unsigned char>(out[0]) == 0xef &&
        static_cast<unsigned char>(out[1]) == 0xbb && static_cast<unsigned char>(out[2]) == 0xbf) {
        out.erase(0, 3);
    }
    return true;
}
const Json* field(const Json& object, const char* name) { auto it = object.o.find(name); return it == object.o.end() ? nullptr : &it->second; }
bool string_field(const Json& object, const char* name, std::string& out, bool required = true) { const Json* value = field(object, name); if (!value) return !required; if (value->kind != Json::string_value) return false; out = value->s; return true; }
bool integer_field(const Json& object, const char* name, uintptr_t& out, bool required = true) { const Json* value = field(object, name); if (!value) return !required; if (value->kind == Json::number_value) { if (value->n < 0 || value->n > (double)UINTPTR_MAX) return false; out = (uintptr_t)value->n; return true; } if (value->kind == Json::string_value) { char* end = nullptr; unsigned long long parsed = strtoull(value->s.c_str(), &end, 0); if (!end || *end) return false; out = (uintptr_t)parsed; return true; } return false; }
std::wstring wide_from_utf8(const std::string& value) { int n = MultiByteToWideChar(CP_UTF8, 0, value.data(), (int)value.size(), nullptr, 0); std::wstring out(n, L'\0'); if (n) MultiByteToWideChar(CP_UTF8, 0, value.data(), (int)value.size(), out.data(), n); return out; }
Probe::Kind probe_kind(const std::string& name) { if (name == "writer_anchor") return Probe::anchor; if (name == "c280_entry") return Probe::c280_entry; if (name == "cardinal_10760") return Probe::cardinal_10760; if (name == "d3b0_entry") return Probe::d3b0_entry; if (name == "da50_entry") return Probe::da50_entry; if (name == "fef0_entry") return Probe::fef0_entry; if (name == "e170_entry") return Probe::e170_entry; if (name == "e170_return") return Probe::e170_return; if (name == "f270_entry") return Probe::f270_entry; if (name == "f270_return") return Probe::f270_return; if (name == "e3a0_entry") return Probe::e3a0_entry; if (name == "e3a0_return0" || name == "e3a0_return1") return Probe::e3a0_return; throw std::runtime_error("unsupported probe name"); }

Config parse_config(const std::string& raw) {
    Json root; if (!JsonParser(raw).parse(root) || root.kind != Json::object_value) throw std::runtime_error("config JSON parse failed"); Config c;
    if (!string_field(root, "run_id", c.run_id) || !string_field(root, "case_id", c.case_id) || !string_field(root, "module", c.module) || !string_field(root, "sha256", c.sha256) || !string_field(root, "renderer", c.renderer)) throw std::runtime_error("run_id/case_id/module/sha256/renderer required"); c.sha256 = lower(c.sha256);
    uintptr_t value = 0; if (!integer_field(root, "ae_pid", value) || value > 0xffffffffu) throw std::runtime_error("ae_pid required"); c.ae_pid = (DWORD)value;
    if (!integer_field(root, "project_bpc", value) || value > 128) throw std::runtime_error("project_bpc required"); c.project_bpc = (unsigned)value;
    if (!integer_field(root, "target_x", value)) throw std::runtime_error("target_x required"); c.target_x = (unsigned)value;
    if (!integer_field(root, "target_y", value)) throw std::runtime_error("target_y required"); c.target_y = (unsigned)value;
    if (c.target_x != 91 || c.target_y != 841) throw std::runtime_error("only target x=91 y=841 is supported");
    std::string output; if (!string_field(root, "output_dir", output)) throw std::runtime_error("output_dir required"); c.output_dir = wide_from_utf8(output); if (c.output_dir.empty()) throw std::runtime_error("output_dir empty");
    if (const Json* timeout = field(root, "timeout_ms")) { if (timeout->kind != Json::number_value || timeout->n < 1000 || timeout->n > 3600000) throw std::runtime_error("timeout_ms invalid"); c.timeout_ms = (DWORD)timeout->n; }
    const Json* probes = field(root, "probes"); if (!probes || probes->kind != Json::array_value) throw std::runtime_error("probes required");
    for (const Json& item : probes->a) { if (item.kind != Json::object_value) throw std::runtime_error("probe must be object"); std::string name; if (!string_field(item, "name", name)) throw std::runtime_error("probe name required"); Probe p{probe_kind(name), name, 0, 0, false}; if (!integer_field(item, "rva", p.rva)) throw std::runtime_error("probe rva required"); p.returns = p.kind == Probe::e170_return || p.kind == Probe::f270_return || p.kind == Probe::e3a0_return; if (p.kind == Probe::e170_entry || p.kind == Probe::f270_entry || p.kind == Probe::e3a0_entry) { if (!integer_field(item, "return_rva", p.return_rva)) throw std::runtime_error("entry return_rva required"); } c.probes.push_back(p); }
    const struct { const char* name; uintptr_t rva; } upstream_defaults[] = {{"c280_entry", 0xc280}, {"cardinal_10760", 0x10760}, {"d3b0_entry", 0xd3b0}, {"da50_entry", 0xda50}, {"fef0_entry", 0xfef0}};
    for (const auto& required_probe : upstream_defaults) { bool present = false; for (const Probe& p : c.probes) if (p.name == required_probe.name) present = true; if (!present) c.probes.push_back({probe_kind(required_probe.name), required_probe.name, required_probe.rva, 0, false}); }
    const char* required[] = {"writer_anchor", "c280_entry", "cardinal_10760", "d3b0_entry", "da50_entry", "fef0_entry", "e170_entry", "e170_return", "f270_entry", "f270_return", "e3a0_entry", "e3a0_return0", "e3a0_return1"}; for (const char* name : required) { unsigned count = 0; for (const Probe& p : c.probes) if (p.name == name) ++count; if (count != 1) throw std::runtime_error(std::string("probe cardinality invalid for ") + name); }
    const auto rva_of = [&](const char* name) -> uintptr_t { for (const Probe& p : c.probes) if (p.name == name) return p.rva; return UINTPTR_MAX; };
    if (rva_of("writer_anchor") != 0x350b || rva_of("c280_entry") != 0xc280 || rva_of("cardinal_10760") != 0x10760 || rva_of("d3b0_entry") != 0xd3b0 || rva_of("da50_entry") != 0xda50 || rva_of("fef0_entry") != 0xfef0 || rva_of("e170_entry") != 0xe170 || rva_of("e170_return") != 0xf284 || rva_of("f270_entry") != 0xf270 || rva_of("f270_return") != 0xff5b || rva_of("e3a0_entry") != 0xe3a0 || rva_of("e3a0_return0") != 0xe3f4 || rva_of("e3a0_return1") != 0xe420) throw std::runtime_error("concrete smoother2 probe RVA contract mismatch");
    if (rva_of("e170_entry") == UINTPTR_MAX || rva_of("f270_entry") == UINTPTR_MAX || rva_of("e3a0_entry") == UINTPTR_MAX) throw std::runtime_error("entry RVA missing");
    for (const Probe& p : c.probes) if ((p.name == "e170_entry" && p.return_rva != rva_of("e170_return")) || (p.name == "f270_entry" && p.return_rva != rva_of("f270_return")) || (p.name == "e3a0_entry" && p.return_rva != rva_of("f270_return"))) throw std::runtime_error("entry/return RVA relation mismatch");
    return c;
}

std::string sha256_file(const std::wstring& path) {
    HANDLE file = CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr); if (file == INVALID_HANDLE_VALUE) return {};
    BCRYPT_ALG_HANDLE algorithm = nullptr; BCRYPT_HASH_HANDLE hash = nullptr; DWORD object_size = 0, returned = 0; std::string result;
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) || BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH, (PUCHAR)&object_size, sizeof(object_size), &returned, 0)) { CloseHandle(file); return {}; }
    std::vector<BYTE> object(object_size), digest(32); if (BCryptCreateHash(algorithm, &hash, object.data(), object_size, nullptr, 0, 0)) { BCryptCloseAlgorithmProvider(algorithm, 0); CloseHandle(file); return {}; }
    BYTE buffer[65536]; DWORD read = 0; bool ok = true; for (;;) { if (!ReadFile(file, buffer, sizeof(buffer), &read, nullptr)) { ok = false; break; } if (!read) break; if (BCryptHashData(hash, buffer, read, 0)) { ok = false; break; } }
    if (ok && !BCryptFinishHash(hash, digest.data(), (ULONG)digest.size(), 0)) { std::ostringstream text; text << std::hex << std::setfill('0'); for (BYTE b : digest) text << std::setw(2) << (int)b; result = text.str(); }
    BCryptDestroyHash(hash); BCryptCloseAlgorithmProvider(algorithm, 0); CloseHandle(file); return result;
}

struct Observation {
    enum Type { bind, c280_entry, cardinal_10760, d3b0_entry, da50_entry, fef0_entry, e170_entry, e170_return, f270_entry, f270_return, e3a0_entry, e3a0_return } type;
    uintptr_t return_address = 0, site = 0, class_base = 0, class_stride = 0, center = 0, previous = 0, left = 0, producer = 0, vertex_storage = 0, p2 = 0;
    BYTE center_b0 = 0, previous_b0 = 0, left_b1 = 0;
    BYTE class_bytes[4]{}, previous_bytes[4]{}, left_bytes[4]{};
    BYTE rax_low = 0;
    DWORD e170_c = 0, vertex_count = 0, rgba[4]{}, weight = 0;
    DWORD x = 0, y = 0;
    int32_t descriptor[6]{};
    int32_t cplane_w = 0, cplane_h = 0;
    uintptr_t source_plane = 0, config_pointer = 0, grid_pointer = 0, input_pointer = 0;
    int32_t input_x = 0, input_y = 0, input_third = 0, result_x = 0, result_y = 0, result_class = 0, dispatch_key = 0;
    bool input_third_available = false, result_available = false, c280_index_inputs_available = false;
};
constexpr LONG kQueueCapacity = 32;
constexpr size_t kMaxProbeCount = 16;
constexpr size_t kMaxAnchorSamples = 32;
Observation g_queue[kQueueCapacity]; volatile LONG g_queue_write = 0, g_queue_read = 0;
volatile LONG g_raw_hits[kMaxProbeCount]{};
DWORD g_anchor_x[kMaxAnchorSamples]{}, g_anchor_y[kMaxAnchorSamples]{};
volatile LONG g_anchor_ready[kMaxAnchorSamples]{};
volatile LONG g_sequence = 0; // legacy chain: 0 bind, 1 f270 entry, 2 e170 entry, 3 e170 return, 4 e3a0 entry, 5 e3a0 return, 6 f270 return, 7 complete
volatile LONG g_upstream_c280 = 0, g_upstream_10760 = 0, g_upstream_d3b0 = 0, g_upstream_da50 = 0, g_upstream_fef0 = 0;
enum FailureCode { failure_none, failure_concurrent, failure_memory, failure_queue, failure_patch, failure_cas };
volatile LONG g_failed = 0, g_failure_code = failure_none, g_step_owner = 0, g_stage_thread = 0, g_final_step_done = 0;
volatile LONG g_initialize_state = 0;
PVOID g_veh = nullptr; std::vector<Installed> g_installed; Config g_config; HMODULE g_module = nullptr; uintptr_t g_module_base = 0; std::ofstream g_trace, g_jsonl;
wchar_t g_config_path[kConfigPathCapacity]{}; uintptr_t g_producer_struct = 0;
thread_local uintptr_t g_step_address = 0; thread_local bool g_skip_rearm = false;
template<class T> bool safe_read(uintptr_t address, T& value) { __try { value = *reinterpret_cast<const T*>(address); return true; } __except (EXCEPTION_EXECUTE_HANDLER) { value = T{}; return false; } }
void set_failure(FailureCode code) { InterlockedCompareExchange(&g_failure_code, code, failure_none); InterlockedExchange(&g_failed, 1); }
const char* failure_detail() { switch ((FailureCode)InterlockedCompareExchange(&g_failure_code, 0, 0)) { case failure_concurrent: return "concurrent breakpoint ownership conflict"; case failure_memory: return "memory read failed for matched expected event"; case failure_queue: return "observation queue overflow"; case failure_patch: return "breakpoint patch/rearm failure"; case failure_cas: return "impossible sequence CAS race"; default: return "collector failure"; } }
bool queue_observation(const Observation& observation) { LONG write = InterlockedCompareExchange(&g_queue_write, 0, 0); LONG read = InterlockedCompareExchange(&g_queue_read, 0, 0); if (write - read >= kQueueCapacity) { set_failure(failure_queue); return false; } g_queue[write % kQueueCapacity] = observation; InterlockedExchange(&g_queue_write, write + 1); return true; }
bool pop_observation(Observation& observation) { LONG read = InterlockedCompareExchange(&g_queue_read, 0, 0); LONG write = InterlockedCompareExchange(&g_queue_write, 0, 0); if (read == write) return false; observation = g_queue[read % kQueueCapacity]; InterlockedExchange(&g_queue_read, read + 1); return true; }
std::string identity() { std::ostringstream out; out << "run_id=" << g_config.run_id << " ae_pid=" << g_config.ae_pid << " module_base=0x" << std::hex << g_module_base << " aex_sha256=" << g_config.sha256 << " project_bpc=" << std::dec << g_config.project_bpc << " renderer=" << g_config.renderer << " case_id=" << g_config.case_id << " witness_id=" << kWitnessId; return out.str(); }
void write_status(const char* state, const std::string& detail = {}) {
    std::wstring final_path = g_config.output_dir + L"\\collector_status.json";
    std::wstring temp_path = g_config.output_dir + L"\\collector_status.json.tmp." + std::to_wstring(GetCurrentProcessId()) + L"." + std::to_wstring(GetCurrentThreadId());
    std::ofstream out(temp_path, std::ios::trunc);
    if (!out) return;
    out << "{\"status\":\"" << state << "\",\"run_id\":\"" << escape_json(g_config.run_id) << "\",\"ae_pid\":" << g_config.ae_pid << ",\"case_id\":\"" << escape_json(g_config.case_id) << "\",\"module_base\":\"0x" << std::hex << g_module_base << "\",\"aex_sha256\":\"" << g_config.sha256 << "\"";
    if (!detail.empty()) out << ",\"detail\":\"" << escape_json(detail) << "\"";
    out << ",\"raw_hit_counts\":{";
    for (size_t i = 0; i < g_config.probes.size() && i < kMaxProbeCount; ++i) {
        if (i) out << ',';
        out << '\"' << escape_json(g_config.probes[i].name) << "\":" << std::dec << InterlockedCompareExchange(&g_raw_hits[i], 0, 0);
    }
    out << '}';
    out << ",\"anchor_samples\":[";
    bool first_anchor_sample = true;
    for (size_t i = 0; i < kMaxAnchorSamples; ++i) {
        if (!InterlockedCompareExchange(&g_anchor_ready[i], 0, 0)) continue;
        if (!first_anchor_sample) out << ',';
        out << '[' << g_anchor_x[i] << ',' << g_anchor_y[i] << ']';
        first_anchor_sample = false;
    }
    out << ']';
    if (!strcmp(state, "ok")) out << ",\"hit_counts\":{\"bind\":1,\"c280_entry\":1,\"cardinal_10760\":1,\"d3b0_entry\":1,\"da50_entry\":1,\"fef0_entry\":1,\"e170_entry\":1,\"e170_return\":1,\"f270_entry\":1,\"f270_return\":1,\"e3a0_entry\":1,\"e3a0_return\":1}";
    out << "}\n";
    out.flush(); out.close();
    if (!out || !MoveFileExW(temp_path.c_str(), final_path.c_str(), MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) DeleteFileW(temp_path.c_str());
}
void json_observation(const Observation& o) { if (!g_jsonl) return; g_jsonl << "{\"stage\":\""; const char* stage = o.type == Observation::bind ? "bind" : o.type == Observation::c280_entry ? "c280_entry" : o.type == Observation::cardinal_10760 ? "cardinal_10760" : o.type == Observation::d3b0_entry ? "d3b0_entry" : o.type == Observation::da50_entry ? "da50_entry" : o.type == Observation::fef0_entry ? "fef0_entry" : o.type == Observation::e170_entry ? "e170_entry" : o.type == Observation::e170_return ? "e170_return" : o.type == Observation::f270_entry ? "f270_entry" : o.type == Observation::f270_return ? "f270_return" : o.type == Observation::e3a0_entry ? "e3a0_entry" : "e3a0_return"; g_jsonl << stage << "\",\"run_id\":\"" << escape_json(g_config.run_id) << "\",\"ae_pid\":" << g_config.ae_pid << ",\"case_id\":\"" << escape_json(g_config.case_id) << "\"}\n"; g_jsonl.flush(); }
void trace_observation(const Observation& o) {
    if (!g_trace) return; const std::string id = identity();
    if (o.type == Observation::bind) g_trace << "S2_PRODUCER_BIND " << id << " stage=bind x=91 y=841 idx=105 expected_descriptor_hint=91,841,1,91,843,5 writer_hook_rva=350b binding_expression=writer_xy_anchor_then_producer_return_address pointer_context=rsp+0x34_x_rsp+0x38_y\n";
    else if (o.type == Observation::c280_entry) g_trace << "S2_UPSTREAM_C280 " << id << " stage=c280_entry hook_rva=c280 caller_x=" << o.x << " caller_y=" << o.y << " source_plane=0x" << std::hex << o.source_plane << " class_plane=0x" << o.class_base << " class_stride=" << std::dec << o.class_stride << " cplane_w=" << o.cplane_w << " cplane_h=" << o.cplane_h << " config_pointer=0x" << std::hex << o.config_pointer << " index_inputs=unavailable index_inputs_proven=false\n";
    else if (o.type == Observation::cardinal_10760) g_trace << "S2_UPSTREAM_10760 " << id << " stage=cardinal_10760 hook_rva=10760 starting_center=" << o.input_x << "," << o.input_y << " class_plane=0x" << std::hex << o.class_base << " class_stride=" << std::dec << o.class_stride << " cplane_w=" << o.cplane_w << " cplane_h=" << o.cplane_h << " scanner_grid=stack_local\n";
    else if (o.type == Observation::d3b0_entry || o.type == Observation::da50_entry) { const char* name = o.type == Observation::d3b0_entry ? "D3B0" : "DA50"; g_trace << "S2_UPSTREAM_" << name << " " << id << " stage=" << (o.type == Observation::d3b0_entry ? "d3b0_entry" : "da50_entry") << " hook_rva=" << (o.type == Observation::d3b0_entry ? "d3b0" : "da50") << " input_xy=" << o.input_x << "," << o.input_y << " input_third=unavailable result_triple=" << (o.result_available ? (std::to_string(o.result_x) + "," + std::to_string(o.result_y) + "," + std::to_string(o.result_class)) : "deferred_to_fef0_descriptor") << "\n"; }
    else if (o.type == Observation::fef0_entry) g_trace << "S2_UPSTREAM_FEF0 " << id << " stage=fef0_entry hook_rva=fef0 descriptor_before=" << std::dec << o.descriptor[0] << "," << o.descriptor[1] << "," << o.descriptor[2] << "," << o.descriptor[3] << "," << o.descriptor[4] << "," << o.descriptor[5] << " d3b0_return_triple=" << o.descriptor[0] << "," << o.descriptor[1] << "," << o.descriptor[2] << " da50_return_triple=" << o.descriptor[3] << "," << o.descriptor[4] << "," << o.descriptor[5] << " return_triples_source=fef0_p2_descriptor_before dispatch_key=" << o.dispatch_key << " dispatch_key_expression=(p2[2]-1)+p2[5]*10\n";
    else if (o.type == Observation::e170_entry) { g_trace << "S2_PRODUCER_E170_ENTRY " << id << " stage=e170_entry hook_rva=e170 return_address=0x" << std::hex << o.return_address << " p2_ptr=0x" << o.p2 << " descriptor=" << std::dec << o.descriptor[0] << "," << o.descriptor[1] << "," << o.descriptor[2] << "," << o.descriptor[3] << "," << o.descriptor[4] << "," << o.descriptor[5] << " sample_x=" << o.descriptor[0] << " sample_y=" << o.descriptor[1] << " cplane_w=" << o.cplane_w << " cplane_h=" << o.cplane_h << " class_base=0x" << std::hex << o.class_base << " class_stride=0x" << o.class_stride << " center_addr=0x" << o.center << " prev_addr=0x" << o.previous << " left_addr=0x" << o.left << " center_b0=" << std::dec << (unsigned)o.center_b0 << " prev_b0=" << (unsigned)o.previous_b0 << " left_b1=" << (unsigned)o.left_b1 << " center_class_bytes=" << (unsigned)o.class_bytes[0] << "," << (unsigned)o.class_bytes[1] << "," << (unsigned)o.class_bytes[2] << "," << (unsigned)o.class_bytes[3] << " prev_class_bytes=" << (unsigned)o.previous_bytes[0] << "," << (unsigned)o.previous_bytes[1] << "," << (unsigned)o.previous_bytes[2] << "," << (unsigned)o.previous_bytes[3] << " left_class_bytes=" << (unsigned)o.left_bytes[0] << "," << (unsigned)o.left_bytes[1] << "," << (unsigned)o.left_bytes[2] << "," << (unsigned)o.left_bytes[3] << " class_base_offset=18 class_stride_offset=28 p2_source=rdx\n"; }
    else if (o.type == Observation::e170_return) g_trace << "S2_PRODUCER_E170_RETURN " << id << " stage=e170_return hook_rva=e170 return_site=f284 return_rax=0x" << std::hex << o.return_address << " e170_c=" << std::dec << o.e170_c << "\n";
    else if (o.type == Observation::f270_entry) g_trace << "S2_PRODUCER_F270_ENTRY " << id << " stage=f270_entry hook_rva=f270 return_address=0x" << std::hex << o.return_address << " producer_struct=0x" << o.producer << "\n";
    else if (o.type == Observation::f270_return) g_trace << "S2_PRODUCER_F270_RETURN " << id << " stage=f270_return hook_rva=f270 return_site=ff5b return_rax=0x" << std::hex << o.return_address << " return_low=" << std::dec << (unsigned)o.rax_low << " vertex_storage=0x" << std::hex << o.vertex_storage << " vertex_count=" << std::dec << o.vertex_count << " first_vertex_rgba_words=" << std::hex << std::setfill('0') << std::setw(8) << o.rgba[0] << "," << std::setw(8) << o.rgba[1] << "," << std::setw(8) << o.rgba[2] << "," << std::setw(8) << o.rgba[3] << " weight_word=" << std::setw(8) << o.weight << "\n";
    else if (o.type == Observation::e3a0_entry) g_trace << "S2_PRODUCER_E3A0_ENTRY " << id << " stage=e3a0_entry hook_rva=e3a0 return_address=0x" << std::hex << o.return_address << " producer_struct=0x" << o.producer << "\n";
    else g_trace << "S2_PRODUCER_E3A0_RETURN " << id << " stage=e3a0_return hook_rva=e3a0 return_site=" << std::hex << o.site << " return_rax=0x" << o.return_address << " return_low=" << std::dec << (unsigned)o.rax_low << " vertex_storage=0x" << std::hex << o.vertex_storage << " vertex_count=" << std::dec << o.vertex_count << " first_vertex_rgba_words=" << std::hex << std::setfill('0') << std::setw(8) << o.rgba[0] << "," << std::setw(8) << o.rgba[1] << "," << std::setw(8) << o.rgba[2] << "," << std::setw(8) << o.rgba[3] << " weight_word=" << std::setw(8) << o.weight << "\n";
    g_trace.flush();
}

bool read_vertex(Observation& o) { o.vertex_storage = o.producer + 0x40; return safe_read(o.producer + 0x130, o.vertex_count) && safe_read(o.producer + 0x40, o.rgba[0]) && safe_read(o.producer + 0x44, o.rgba[1]) && safe_read(o.producer + 0x48, o.rgba[2]) && safe_read(o.producer + 0x4c, o.rgba[3]) && safe_read(o.producer + 0x50, o.weight); }
const Probe* probe_for(Probe::Kind kind) { for (const Probe& p : g_config.probes) if (p.kind == kind) return &p; return nullptr; }

LONG CALLBACK veh(PEXCEPTION_POINTERS exception) {
    if (!exception || !exception->ExceptionRecord || !exception->ContextRecord) return EXCEPTION_CONTINUE_SEARCH; CONTEXT& context = *exception->ContextRecord; DWORD tid = GetCurrentThreadId();
    if (exception->ExceptionRecord->ExceptionCode == EXCEPTION_BREAKPOINT) {
        uintptr_t address = reinterpret_cast<uintptr_t>(exception->ExceptionRecord->ExceptionAddress); const Installed* hit = nullptr; size_t hit_index = 0; for (size_t i = 0; i < g_installed.size(); ++i) if (g_installed[i].address == address) { hit = &g_installed[i]; hit_index = i; break; } if (!hit) return EXCEPTION_CONTINUE_SEARCH;
        LONG raw_ordinal = InterlockedIncrement(&g_raw_hits[hit_index]);
        if (hit->kind == Probe::anchor && raw_ordinal > 0 && raw_ordinal <= static_cast<LONG>(kMaxAnchorSamples)) {
            DWORD x = 0, y = 0;
            if (safe_read(context.Rsp + 0x34, x) && safe_read(context.Rsp + 0x38, y)) {
                size_t sample_index = static_cast<size_t>(raw_ordinal - 1);
                g_anchor_x[sample_index] = x;
                g_anchor_y[sample_index] = y;
                MemoryBarrier();
                InterlockedExchange(&g_anchor_ready[sample_index], 1);
            }
        }
        while (InterlockedCompareExchange(&g_step_owner, (LONG)tid, 0) != 0) SwitchToThread();
        DWORD old = 0;
        if (!VirtualProtect((void*)address, 1, PAGE_EXECUTE_READWRITE, &old)) { set_failure(failure_patch); return EXCEPTION_CONTINUE_SEARCH; }
        *(BYTE*)address = hit->original;
        if (!FlushInstructionCache(GetCurrentProcess(), (void*)address, 1) || !VirtualProtect((void*)address, 1, old, &old)) { set_failure(failure_patch); return EXCEPTION_CONTINUE_SEARCH; }
        context.Rip = address; context.EFlags |= 0x100; g_step_address = address; g_skip_rearm = false;

        LONG state = InterlockedCompareExchange(&g_sequence, 0, 0); Observation observation{}; bool accepted = false;
        if (hit->kind == Probe::anchor && state == 0) {
            DWORD x = 0, y = 0;
            if (safe_read(context.Rsp + 0x34, x) && safe_read(context.Rsp + 0x38, y) && x == 91 && y == 841) {
                observation.type = Observation::bind; observation.x = x; observation.y = y;
                if (InterlockedCompareExchange(&g_sequence, 1, 0) == 0) { InterlockedExchange(&g_stage_thread, (LONG)tid); accepted = true; } else set_failure(failure_cas);
            }
        } else if (hit->kind == Probe::c280_entry && state >= 1 && InterlockedCompareExchange(&g_stage_thread, 0, 0) == (LONG)tid && InterlockedCompareExchange(&g_upstream_c280, 1, 0) == 0) {
            int32_t x = 0, y = 0, width = 0, height = 0, stride = 0;
            uintptr_t source = 0, class_base = 0, config = 0;
            bool ok = safe_read(context.R9, x) && safe_read(context.R9 + 4, y)
                && safe_read(context.Rdx, source) && safe_read(context.R8, class_base)
                && safe_read(context.R8 + 8, width) && safe_read(context.R8 + 12, height)
                && safe_read(context.R8 + 16, stride) && safe_read(context.Rsp + 0x28, config);
            if (!ok) { InterlockedExchange(&g_upstream_c280, 0); set_failure(failure_memory); }
            else { observation.type = Observation::c280_entry; observation.x = (DWORD)x; observation.y = (DWORD)y; observation.source_plane = source; observation.class_base = class_base; observation.cplane_w = width; observation.cplane_h = height; observation.class_stride = (uintptr_t)(uint32_t)stride; observation.config_pointer = config; accepted = true; }
        } else if (hit->kind == Probe::cardinal_10760 && state >= 1 && InterlockedCompareExchange(&g_stage_thread, 0, 0) == (LONG)tid && InterlockedCompareExchange(&g_upstream_c280, 0, 0) == 1 && InterlockedCompareExchange(&g_upstream_10760, 1, 0) == 0) {
            int32_t x = 0, y = 0;
            bool ok = safe_read(context.Rcx + 0x30, x) && safe_read(context.Rcx + 0x34, y)
                && safe_read(context.Rcx + 0x18, observation.class_base) && safe_read(context.Rcx + 0x20, observation.cplane_w)
                && safe_read(context.Rcx + 0x24, observation.cplane_h) && safe_read(context.Rcx + 0x28, observation.class_stride);
            if (!ok) { InterlockedExchange(&g_upstream_10760, 0); set_failure(failure_memory); }
            else { observation.type = Observation::cardinal_10760; observation.input_x = x; observation.input_y = y; accepted = true; }
        } else if ((hit->kind == Probe::d3b0_entry || hit->kind == Probe::da50_entry) && state >= 1 && InterlockedCompareExchange(&g_stage_thread, 0, 0) == (LONG)tid && InterlockedCompareExchange(&g_upstream_10760, 0, 0) == 1 && ((hit->kind == Probe::d3b0_entry && InterlockedCompareExchange(&g_upstream_d3b0, 1, 0) == 0) || (hit->kind == Probe::da50_entry && InterlockedCompareExchange(&g_upstream_d3b0, 0, 0) == 1 && InterlockedCompareExchange(&g_upstream_da50, 1, 0) == 0))) {
            int32_t x = 0, y = 0;
            bool ok = safe_read(context.R8, x) && safe_read(context.R8 + 4, y);
            if (!ok) { if (hit->kind == Probe::d3b0_entry) InterlockedExchange(&g_upstream_d3b0, 0); else InterlockedExchange(&g_upstream_da50, 0); set_failure(failure_memory); }
            else { observation.type = hit->kind == Probe::d3b0_entry ? Observation::d3b0_entry : Observation::da50_entry; observation.input_pointer = context.R8; observation.input_x = x; observation.input_y = y; observation.result_available = false; accepted = true; }
        } else if (hit->kind == Probe::fef0_entry && state >= 1 && InterlockedCompareExchange(&g_stage_thread, 0, 0) == (LONG)tid && InterlockedCompareExchange(&g_upstream_da50, 0, 0) == 1 && InterlockedCompareExchange(&g_upstream_fef0, 1, 0) == 0) {
            bool ok = true;
            observation.type = Observation::fef0_entry;
            observation.p2 = context.Rdx;
            for (size_t i = 0; i < 6; ++i) ok = ok && safe_read(context.Rdx + i * sizeof(int32_t), observation.descriptor[i]);
            if (ok) observation.dispatch_key = (observation.descriptor[2] - 1) + observation.descriptor[5] * 10;
            if (!ok) { InterlockedExchange(&g_upstream_fef0, 0); set_failure(failure_memory); } else accepted = true;
        } else if (!hit->returns && hit->kind == Probe::f270_entry && state == 1 && InterlockedCompareExchange(&g_stage_thread, 0, 0) == (LONG)tid) {
            uintptr_t return_address = 0;
            if (!safe_read(context.Rsp, return_address)) set_failure(failure_memory);
            else if (return_address == g_module_base + probe_for(Probe::f270_return)->rva) {
                observation.type = Observation::f270_entry; observation.return_address = return_address; observation.producer = context.Rcx;
                if (InterlockedCompareExchange(&g_sequence, 2, 1) == 1) { g_producer_struct = context.Rcx; accepted = true; }
                else set_failure(failure_cas);
            }
        } else if (!hit->returns && hit->kind == Probe::e170_entry && state == 2 && InterlockedCompareExchange(&g_stage_thread, 0, 0) == (LONG)tid) {
            uintptr_t return_address = 0;
            if (!safe_read(context.Rsp, return_address)) set_failure(failure_memory);
            else if (return_address == g_module_base + probe_for(Probe::e170_return)->rva) {
                observation.type = Observation::e170_entry; observation.return_address = return_address;
                uint32_t class_stride = 0;
                observation.p2 = context.Rdx;
                bool ok = safe_read(context.Rcx + 0x18, observation.class_base)
                    && safe_read(context.Rcx + 0x20, observation.cplane_w)
                    && safe_read(context.Rcx + 0x24, observation.cplane_h)
                    && safe_read(context.Rcx + 0x28, class_stride);
                for (size_t i = 0; ok && i < 6; ++i) ok = safe_read(context.Rdx + i * sizeof(int32_t), observation.descriptor[i]);
                if (ok) {
                    observation.class_stride = class_stride;
                    const int32_t x = observation.descriptor[0], y = observation.descriptor[1];
                    ok = x > 0 && y > 0 && x < observation.cplane_w && y < observation.cplane_h;
                    if (ok) {
                        observation.center = observation.class_base + static_cast<uintptr_t>(y) * observation.class_stride + static_cast<uintptr_t>(x) * 4;
                        observation.previous = observation.class_base + static_cast<uintptr_t>(y - 1) * observation.class_stride + static_cast<uintptr_t>(x) * 4;
                        uintptr_t left_pixel = observation.class_base + static_cast<uintptr_t>(y) * observation.class_stride + static_cast<uintptr_t>(x - 1) * 4;
                        observation.left = left_pixel + 1;
                        ok = safe_read(observation.center, observation.center_b0) && safe_read(observation.previous, observation.previous_b0) && safe_read(observation.left, observation.left_b1)
                            && safe_read(observation.center, observation.class_bytes[0]) && safe_read(observation.center + 1, observation.class_bytes[1]) && safe_read(observation.center + 2, observation.class_bytes[2]) && safe_read(observation.center + 3, observation.class_bytes[3])
                            && safe_read(observation.previous, observation.previous_bytes[0]) && safe_read(observation.previous + 1, observation.previous_bytes[1]) && safe_read(observation.previous + 2, observation.previous_bytes[2]) && safe_read(observation.previous + 3, observation.previous_bytes[3])
                            && safe_read(left_pixel, observation.left_bytes[0]) && safe_read(left_pixel + 1, observation.left_bytes[1]) && safe_read(left_pixel + 2, observation.left_bytes[2]) && safe_read(left_pixel + 3, observation.left_bytes[3]);
                    }
                }
                if (!ok) set_failure(failure_memory);
                else if (InterlockedCompareExchange(&g_sequence, 3, 2) == 2) accepted = true;
                else set_failure(failure_cas);
            }
        } else if (hit->returns && hit->kind == Probe::e170_return && state == 3 && InterlockedCompareExchange(&g_stage_thread, 0, 0) == (LONG)tid) {
            observation.type = Observation::e170_return; observation.site = address - g_module_base; observation.return_address = context.Rax; observation.rax_low = (BYTE)(context.Rax & 0xff); observation.e170_c = observation.rax_low;
            if (InterlockedCompareExchange(&g_sequence, 4, 3) == 3) accepted = true; else set_failure(failure_cas);
        } else if (!hit->returns && hit->kind == Probe::e3a0_entry && state == 4 && InterlockedCompareExchange(&g_stage_thread, 0, 0) == (LONG)tid) {
            uintptr_t return_address = 0;
            if (!safe_read(context.Rsp, return_address)) set_failure(failure_memory);
            else if (return_address == g_module_base + probe_for(Probe::f270_return)->rva) {
                observation.type = Observation::e3a0_entry; observation.return_address = return_address; observation.producer = g_producer_struct;
                if (InterlockedCompareExchange(&g_sequence, 5, 4) == 4) accepted = true;
                else set_failure(failure_cas);
            }
        } else if (hit->returns && hit->kind == Probe::e3a0_return && state == 5 && InterlockedCompareExchange(&g_stage_thread, 0, 0) == (LONG)tid) {
            observation.type = Observation::e3a0_return; observation.site = address - g_module_base; observation.return_address = context.Rax; observation.rax_low = (BYTE)(context.Rax & 0xff); observation.producer = g_producer_struct;
            if (!read_vertex(observation)) set_failure(failure_memory);
            else if (InterlockedCompareExchange(&g_sequence, 6, 5) == 5) accepted = true; else set_failure(failure_cas);
        } else if (hit->returns && hit->kind == Probe::f270_return && state == 6 && InterlockedCompareExchange(&g_stage_thread, 0, 0) == (LONG)tid) {
            observation.type = Observation::f270_return; observation.site = address - g_module_base; observation.return_address = context.Rax; observation.rax_low = (BYTE)(context.Rax & 0xff); observation.producer = g_producer_struct;
            if (!read_vertex(observation)) set_failure(failure_memory);
            else if (InterlockedCompareExchange(&g_sequence, 7, 6) == 6) { accepted = true; g_skip_rearm = true; }
            else set_failure(failure_cas);
        }
        if (accepted) queue_observation(observation);
        return EXCEPTION_CONTINUE_EXECUTION;
    }
    if (exception->ExceptionRecord->ExceptionCode == EXCEPTION_SINGLE_STEP && g_step_address) {
        if (!g_skip_rearm) {
            bool found = false;
            for (const Installed& item : g_installed) if (item.address == g_step_address) { found = true; DWORD old = 0; if (!VirtualProtect((void*)item.address, 1, PAGE_EXECUTE_READWRITE, &old)) set_failure(failure_patch); else { *(BYTE*)item.address = 0xCC; if (!FlushInstructionCache(GetCurrentProcess(), (void*)item.address, 1) || !VirtualProtect((void*)item.address, 1, old, &old)) set_failure(failure_patch); } break; }
            if (!found) set_failure(failure_patch);
        } else InterlockedExchange(&g_final_step_done, 1);
        g_step_address = 0; g_skip_rearm = false; InterlockedExchange(&g_step_owner, 0); context.EFlags &= ~0x100; return EXCEPTION_CONTINUE_EXECUTION;
    }
    return EXCEPTION_CONTINUE_SEARCH;
}

void restore_all() { for (const Installed& item : g_installed) { DWORD old = 0; if (VirtualProtect((void*)item.address, 1, PAGE_EXECUTE_READWRITE, &old)) { *(BYTE*)item.address = item.original; FlushInstructionCache(GetCurrentProcess(), (void*)item.address, 1); VirtualProtect((void*)item.address, 1, old, &old); } } }
void fail(const std::string& detail) { InterlockedExchange(&g_failed, 1); restore_all(); if (g_veh) { RemoveVectoredExceptionHandler(g_veh); g_veh = nullptr; } write_status("failed", detail); }
bool arm() {
    g_module = GetModuleHandleW(wide_from_utf8(g_config.module).c_str()); if (!g_module) { fail("OLMSmoother2.aex not loaded"); return false; } g_module_base = (uintptr_t)g_module; MODULEINFO info{}; if (!GetModuleInformation(GetCurrentProcess(), g_module, &info, sizeof(info))) { fail("GetModuleInformation failed"); return false; }
    wchar_t module_path[32768]{}; if (!GetModuleFileNameW(g_module, module_path, ARRAYSIZE(module_path))) { fail("module path lookup failed"); return false; } std::string actual = lower(sha256_file(std::wstring(module_path))); if (actual.empty() || actual != g_config.sha256) { fail("module path=" + utf8(std::wstring(module_path)) + " base=0x" + [&]{ std::ostringstream s; s << std::hex << g_module_base; return s.str(); }() + "; SHA-256 mismatch"); return false; }
    if (GetFileAttributesW(g_config.output_dir.c_str()) == INVALID_FILE_ATTRIBUTES && !CreateDirectoryW(g_config.output_dir.c_str(), nullptr)) { fail("output_dir unavailable"); return false; }
    g_trace.open(g_config.output_dir + L"\\collector_trace.txt", std::ios::app); g_jsonl.open(g_config.output_dir + L"\\collector.jsonl", std::ios::app); if (!g_trace || !g_jsonl) { fail("trace output unavailable"); return false; }
    try {
        if (g_config.probes.size() > kMaxProbeCount) { fail("too many probes for raw-hit accounting"); return false; }
        g_installed.clear();
        g_installed.reserve(g_config.probes.size());
        for (size_t i = 0; i < kMaxProbeCount; ++i) InterlockedExchange(&g_raw_hits[i], 0);
        for (size_t i = 0; i < kMaxAnchorSamples; ++i) InterlockedExchange(&g_anchor_ready[i], 0);
        InterlockedExchange(&g_sequence, 0); InterlockedExchange(&g_upstream_c280, 0); InterlockedExchange(&g_upstream_10760, 0); InterlockedExchange(&g_upstream_d3b0, 0); InterlockedExchange(&g_upstream_da50, 0); InterlockedExchange(&g_upstream_fef0, 0); InterlockedExchange(&g_final_step_done, 0);
        for (const Probe& p : g_config.probes) {
            if (p.rva >= info.SizeOfImage || p.rva > UINTPTR_MAX - g_module_base) { fail("probe RVA outside module"); return false; }
            uintptr_t address = g_module_base + p.rva;
            MEMORY_BASIC_INFORMATION mbi{};
            if (!VirtualQuery((void*)address, &mbi, sizeof(mbi)) || mbi.State != MEM_COMMIT) { fail("probe address is not committed"); return false; }
            g_installed.push_back({address, *(BYTE*)address, p.kind, p.returns});
        }
    } catch (...) { fail("probe storage allocation failed"); return false; }
    g_veh = AddVectoredExceptionHandler(1, veh); if (!g_veh) { fail("AddVectoredExceptionHandler failed"); return false; }
    for (const Installed& item : g_installed) {
        DWORD old = 0;
        if (!VirtualProtect((void*)item.address, 1, PAGE_EXECUTE_READWRITE, &old)) { fail("probe page protection change failed"); return false; }
        *(BYTE*)item.address = 0xCC;
        if (!FlushInstructionCache(GetCurrentProcess(), (void*)item.address, 1) || !VirtualProtect((void*)item.address, 1, old, &old)) { fail("probe cache flush/protection restore failed"); return false; }
    }
    write_status("armed"); return true;
}
void monitor() { ULONGLONG deadline = GetTickCount64() + g_config.timeout_ms; LONG last_raw_total = 0; for (;;) { Observation observation{}; while (pop_observation(observation)) { trace_observation(observation); json_observation(observation); } LONG raw_total = 0; for (size_t i = 0; i < g_config.probes.size(); ++i) raw_total += InterlockedCompareExchange(&g_raw_hits[i], 0, 0); if (raw_total != last_raw_total) { write_status("armed", "raw breakpoint progress"); last_raw_total = raw_total; } if (InterlockedCompareExchange(&g_failed, 0, 0)) { fail(failure_detail()); return; } if (InterlockedCompareExchange(&g_sequence, 0, 0) == 7 && InterlockedCompareExchange(&g_final_step_done, 0, 0)) { /* Other AE render threads may still be inside patched code. Keep VEH/probes alive until this one-case AE process exits; eager restore races those threads. */ if (InterlockedCompareExchange(&g_upstream_c280, 0, 0) && InterlockedCompareExchange(&g_upstream_10760, 0, 0) && InterlockedCompareExchange(&g_upstream_d3b0, 0, 0) && InterlockedCompareExchange(&g_upstream_da50, 0, 0) && InterlockedCompareExchange(&g_upstream_fef0, 0, 0)) { write_status("ok"); return; } fail("upstream origin/descriptor witness incomplete"); return; } if (GetTickCount64() >= deadline) { fail("timeout before complete bind/upstream/f270/e170/e3a0 sequence"); return; } Sleep(5); } }
DWORD WINAPI worker(void*) {
    std::string raw;
    if (!read_file(std::wstring(g_config_path), raw)) {
        std::ofstream error(std::wstring(g_config_path) + L".error.txt", std::ios::binary);
        error << "collector could not read config\n";
        g_config_path[0] = L'\0';
        InterlockedExchange(&g_initialize_state, 0);
        return 0;
    }
    try {
        g_config = parse_config(raw);
        if (g_config.ae_pid != GetCurrentProcessId()) write_status("failed", "ae_pid does not match target process");
        else if (arm()) monitor();
    } catch (const std::exception& error) { write_status("failed", error.what()); }
    g_config_path[0] = L'\0';
    InterlockedExchange(&g_initialize_state, 0);
    return 0;
}

bool copy_config_path(const wchar_t* source) {
    if (!source) return false;
    bool terminated = false;
    __try {
        for (DWORD i = 0; i < kConfigPathCapacity; ++i) {
            wchar_t value = source[i];
            g_config_path[i] = value;
            if (!value) { terminated = true; break; }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        g_config_path[0] = L'\0';
        return false;
    }
    if (!terminated || !((g_config_path[0] >= L'A' && g_config_path[0] <= L'Z') || (g_config_path[0] >= L'a' && g_config_path[0] <= L'z')) || g_config_path[1] != L':' || (g_config_path[2] != L'\\' && g_config_path[2] != L'/')) {
        g_config_path[0] = L'\0';
        return false;
    }
    return true;
}
}

extern "C" __declspec(dllexport) DWORD WINAPI OLMInitializeCollector(void* config_path_wide) {
    if (InterlockedCompareExchange(&g_initialize_state, 1, 0) != 0) return 0;
    if (!copy_config_path(static_cast<const wchar_t*>(config_path_wide))) {
        InterlockedExchange(&g_initialize_state, 0);
        return 0;
    }
    HANDLE thread = CreateThread(nullptr, 0, worker, nullptr, 0, nullptr);
    if (!thread) {
        g_config_path[0] = L'\0';
        InterlockedExchange(&g_initialize_state, 0);
        return 0;
    }
    CloseHandle(thread);
    return kInitializeAccepted;
}

BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) DisableThreadLibraryCalls(instance);
    return TRUE;
}
