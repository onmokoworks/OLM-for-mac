// Diagnostic only. No capture allocation or file I/O unless explicitly enabled.
#pragma once
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <sstream>
#include <iomanip>
#include <locale>
#include <vector>
#include <stdexcept>
#include <unistd.h>
#include <dlfcn.h>
#include <CommonCrypto/CommonDigest.h>
namespace olm_live {
struct Data;
static thread_local Data *active = nullptr;
inline std::string quote(const std::string &s) {
    std::ostringstream o; o << '"';
    for (unsigned char c:s) { if(c=='"'||c=='\\') o << '\\' << c;
        else if(c<32) o << "\\u" << std::hex << std::setw(4) << std::setfill('0') << int(c);
        else o << c; } o << '"'; return o.str();
}
template<class R> std::string rect(const R &r) {
    std::ostringstream o; o << '[' << r.left << ',' << r.top << ',' << r.right << ',' << r.bottom << ']'; return o.str();
}
template<class T> auto field(T *p,int) -> decltype(p->field, std::string()) { return std::to_string(p->field); }
template<class T> std::string field(T *,long) { return "null"; }
template<class T> auto aspect(T *p,int) -> decltype(p->pixel_aspect_ratio, std::string()) {
 return "["+std::to_string(p->pixel_aspect_ratio.num)+","+std::to_string(p->pixel_aspect_ratio.den)+"]";
}
template<class T> std::string aspect(T *,long) { return "null"; }
template<class T> auto total(T *p,int) -> decltype(p->total_time, std::string()) { return std::to_string(p->total_time); }
template<class T> std::string total(T *,long) { return "null"; }
struct Data {
    Data *previous; std::string dir; std::ostringstream meta, parameters;
    bool enabled=false, first=true, failed=false;
 long output_x=0,output_y=0;
    Data(const char *plugin,const char *route,PF_InData *in):previous(active) {
        const char *root=std::getenv("OLM_LIVE_CAPTURE_DIR");
        if(!root || !*root) return;
        try {
            std::string pattern=std::string(root)+"/"+plugin+"-"+route+"-XXXXXX";
            std::vector<char> name(pattern.begin(),pattern.end()); name.push_back(0);
            if(!mkdtemp(name.data())) throw std::runtime_error("mkdtemp");
            dir=name.data(); enabled=true; active=this;
 if(!in)throw std::runtime_error("null host");
 output_x=in->output_origin_x;output_y=in->output_origin_y;
            meta.imbue(std::locale::classic()); parameters.imbue(std::locale::classic());
            meta << std::setprecision(17); parameters << std::setprecision(17);
            Dl_info dl{}; dladdr((void*)&quote,&dl);
            std::string hash; if(dl.dli_fname) {
                FILE *f=fopen(dl.dli_fname,"rb"); if(!f) throw std::runtime_error("build identity open");
                CC_SHA256_CTX ctx; CC_SHA256_Init(&ctx); unsigned char buf[16384], digest[32]; size_t n;
                while((n=fread(buf,1,sizeof(buf),f))) CC_SHA256_Update(&ctx,buf,(CC_LONG)n);
                bool bad=ferror(f); if(fclose(f)) bad=true; if(bad) throw std::runtime_error("build identity read");
                CC_SHA256_Final(digest,&ctx); const char *hex="0123456789abcdef";
                for(auto b:digest) {hash+=hex[b>>4];hash+=hex[b&15];}
            }
            meta << "{\"schema\":1,\"plugin\":" << quote(plugin) << ",\"route\":" << quote(route)
                 << ",\"build\":{\"sha256\":" << quote(hash) << ",\"path\":" << quote(dl.dli_fname?dl.dli_fname:"")
                 << ",\"compiled\":" << quote(__DATE__ " " __TIME__) << "},\"host\":{\"width\":" << in->width
                 << ",\"height\":" << in->height << ",\"downsample\":[[" << in->downsample_x.num << ',' << in->downsample_x.den
                 << "],[" << in->downsample_y.num << ',' << in->downsample_y.den << "]],\"field\":" << field(in,0)
                 << ",\"pixel_aspect\":" << aspect(in,0) << ",\"total_time\":" << total(in,0)
                 << ",\"current_time\":" << in->current_time << ",\"time_step\":" << in->time_step << ",\"time_scale\":" << in->time_scale
                 << ",\"output_origin\":[" << in->output_origin_x << ',' << in->output_origin_y
                 << "],\"source_origin\":[" << in->pre_effect_source_origin_x << ',' << in->pre_effect_source_origin_y << "]}";
        } catch(...) { fail(); }
    }
    void fail() noexcept { failed=true; std::fprintf(stderr,"OLM_LIVE_CAPTURE_DIR: capture write failed (%s)\n",dir.c_str()); }
    ~Data() { if(enabled && !failed) std::fprintf(stderr,"OLM_LIVE_CAPTURE_DIR: incomplete render capture (%s)\n",dir.c_str()); if(active==this)active=previous; }
    void file(const char *name,const void *data,size_t size) {
        FILE *f=fopen((dir+"/"+name).c_str(),"wbx"); if(!f)throw std::runtime_error("open");
        bool bad=fwrite(data,1,size,f)!=size; if(fclose(f))bad=true; if(bad)throw std::runtime_error("write/close");
    }
    void world(const char *name,const PF_EffectWorld *w,int depth) noexcept {
        if(!enabled||failed)return; try {
            if(!w||!w->data||w->height<0||w->rowbytes<=0||w->width<0||size_t(w->rowbytes)<size_t(w->width)*4*(depth/8))throw std::runtime_error("world layout");
            file((std::string(name)+".raw").c_str(),w->data,size_t(w->rowbytes)*w->height);
            meta << ',' << quote(name) << ":{\"width\":" << w->width << ",\"height\":" << w->height << ",\"rowbytes\":" << w->rowbytes
                 << ",\"depth\":" << depth << ",\"origin\":[" << w->origin_x << ',' << w->origin_y << "],\"extent_hint\":" << rect(w->extent_hint) << '}';
        }catch(...){fail();}
    }
    template<class R> void request(const R &r) noexcept { if(enabled&&!failed)try{meta << ",\"request_rect\":" << rect(r);}catch(...){fail();} }
    void value(int slot,const char *kind,const std::string &v) noexcept {
        if(!enabled||failed)return; try{if(!first)parameters<<','; first=false;
            parameters << "{\"slot\":" << slot << ",\"kind\":" << quote(kind) << ",\"value\":" << v << '}';}catch(...){fail();}
    }
    void finish(PF_EffectWorld *out,int depth,PF_Err err) noexcept {
        if(!enabled||failed)return; world("output",out,depth); if(failed)return;
        try { meta << ",\"output_rect\":[" << output_x << ',' << output_y << ',' << output_x+out->width << ',' << output_y+out->height << "],\"render_error\":" << err << ",\"parameters\":[" << parameters.str() << "]}";
            const auto s=meta.str(); file("capture.json",s.data(),s.size()); enabled=false;
        }catch(...){fail();}
    }
};
// Only a pointer and getenv/branches on the disabled path: streams, strings,
// hashing and filesystem activity are all inside the opt-in Data allocation.
struct Capture {
    Data *data=nullptr;
    Capture(const char *plugin,const char *route,PF_InData *in) noexcept {
        const char *root=std::getenv("OLM_LIVE_CAPTURE_DIR");
        if(!root || !*root)return;
        try {data=new Data(plugin,route,in);} catch(...) {
            std::fprintf(stderr,"OLM_LIVE_CAPTURE_DIR: capture allocation failed\n");
        }
    }
    ~Capture() {delete data;}
    Capture(const Capture &)=delete;
    Capture &operator=(const Capture &)=delete;
    void world(const char *n,const PF_EffectWorld *w,int depth) noexcept {if(data)data->world(n,w,depth);}
    template<class R> void request(const R &r) noexcept {if(data)data->request(r);}
    void finish(PF_EffectWorld *w,int depth,PF_Err err) noexcept {if(data)data->finish(w,depth,err);}
};
inline void scalar(int slot,const char *kind,double value) noexcept {
    if(!active)return; try{std::ostringstream s;s.imbue(std::locale::classic());s<<std::setprecision(17)<<value;active->value(slot,kind,s.str());}catch(...){active->fail();}
}
template<class C> void color(int slot,const C &c,const char *kind="c") noexcept {
    if(!active)return;try{std::ostringstream s;s.imbue(std::locale::classic());s<<std::setprecision(17)<<'['<<+c.alpha<<','<<+c.red<<','<<+c.green<<','<<+c.blue<<']';active->value(slot,kind,s.str());}catch(...){active->fail();}
}
}
