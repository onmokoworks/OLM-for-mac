#pragma once
// UI-only translation of 181235bb0 / 1812366b0. No render or saved-data code.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>

namespace olm::kirakira::editor {
struct Rect { int left, top, right, bottom;
    bool contains(int x, int y) const {
        return left <= x && x <= right && top <= y && y <= bottom;
    }
};
constexpr Rect strip{10,5,202,55};
constexpr Rect buttons[] = {{225,35,295,55},{225,60,295,80},{5,80,135,100},{140,80,205,100}};
constexpr const char16_t* captions[] = {u"copy",u"paste",u"randomize",u"flip"};
struct Color { float red, green, blue, alpha; };
struct State { int selected = -1, armed = -1, hover_x = 0, hover_y = 0; };
enum class EventType { hover, single, multiple, drag, release };
struct Event { EventType type; int x, y; };
struct Result { int picker = -1; };
template<class Ramp> struct Clipboard { bool available = false; Ramp data{}; };

template<class Ramp> Rect marker(const Ramp& ramp, unsigned i) {
    const int x = static_cast<int>(10.0f + 192.0f * ramp.stops[i].position);
    return {x-5,60,x+5,70};
}
template<class Ramp> int hit(const Ramp& ramp, int x, int y) {
    for (int i = static_cast<int>(ramp.count)-1; i >= 0; --i)
        if (marker(ramp, i).contains(x,y)) return i;
    return -1;
}
template<class Ramp> void sort(Ramp& ramp) {
    // Original selection/exchange sort, including its equal-position ordering.
    for (unsigned i=0; i<ramp.count; ++i)
        for (unsigned j=i+1; j<ramp.count; ++j)
            if (ramp.stops[j].position < ramp.stops[i].position)
                std::swap(ramp.stops[i], ramp.stops[j]);
}
template<class Stop> Color color(const Stop& s) { return {s.red,s.green,s.blue,s.alpha}; }
template<class Ramp> Color sample(const Ramp& ramp, float position) {
    if (!ramp.count) return {0,0,0,1};
    int lo=-1, hi=-1;
    for (unsigned i=0; i<ramp.count; ++i) {
        float p=ramp.stops[i].position;
        if (p-position <= 0) {
            if (lo<0 || (ramp.stops[lo].position<=p && p!=ramp.stops[lo].position)) lo=i;
        } else if (hi<0 || p<ramp.stops[hi].position) hi=i;
    }
    if (lo<0) return color(ramp.stops[hi]);
    if (hi<0) return color(ramp.stops[lo]);
    const auto a=color(ramp.stops[lo]), b=color(ramp.stops[hi]);
    const float delta=ramp.stops[hi].position-ramp.stops[lo].position;
    const float t=std::fabs(delta)<0.0001f ? 0.0f : (position-ramp.stops[lo].position)/delta;
    return {(b.red-a.red)*t+a.red,(b.green-a.green)*t+a.green,
            (b.blue-a.blue)*t+a.blue,(b.alpha-a.alpha)*t+a.alpha};
}
template<class Stop> void set_color(Stop& s, Color c) {
    s.red=c.red; s.green=c.green; s.blue=c.blue; s.alpha=c.alpha;
}
inline std::uint32_t random_word(std::uint32_t& rng) {
    rng ^= rng<<13; rng ^= rng>>17; rng ^= rng<<5; return rng;
}
template<class Ramp> void randomize(Ramp& ramp, std::uint32_t& rng) {
    rng=(rng>>16 ^ rng ^ 0x3du)*9u;
    rng=(rng>>4 ^ rng)*0x27d4eb2du;
    rng ^= rng>>15;
    for (unsigned i=0; i<ramp.count; ++i) {
        ramp.stops[i].red=static_cast<float>(random_word(rng))*0x1p-32f;
        ramp.stops[i].green=static_cast<float>(random_word(rng))*0x1p-32f;
        ramp.stops[i].blue=static_cast<float>(random_word(rng))*0x1p-32f;
    }
}
template<class Ramp> void flip(Ramp& ramp) {
    for (unsigned i=0; i<ramp.count/2; ++i) {
        auto c=color(ramp.stops[i]);
        set_color(ramp.stops[i],color(ramp.stops[ramp.count-1-i]));
        set_color(ramp.stops[ramp.count-1-i],c);
    }
}
template<class Ramp> Result dispatch(Ramp& ramp, State& state, Clipboard<Ramp>& clipboard,
                                    std::uint32_t& rng, Event e) {
    if (ramp.count>16) return {};
    state.hover_x=e.x; state.hover_y=e.y;
    if (e.type==EventType::hover) return {};
    if (e.type==EventType::single) {
        if (strip.contains(e.x,e.y)) {
            if (ramp.count<16) {
                float p=static_cast<float>(e.x-10)/192.0f;
                auto c=sample(ramp,p);
                auto& s=ramp.stops[ramp.count++]; s.position=p; set_color(s,c);
                state.selected=-1; sort(ramp);
            }
        } else state.selected=hit(ramp,e.x,e.y);
    } else if (e.type==EventType::multiple) {
        int i=hit(ramp,e.x,e.y);
        if (i>=0) return {i};
    } else if (state.selected>=0 && static_cast<unsigned>(state.selected)<ramp.count) {
        if (e.type==EventType::drag) {
            auto& s=ramp.stops[state.selected];
            s.position=std::max(0.0f,std::min(1.0f,static_cast<float>(e.x-10)/192.0f));
            s.alpha=e.y-55>20 ? 0.5f : 1.0f;
        } else if (e.type==EventType::release) {
            if (e.y-55>20) {
                for (unsigned i=state.selected+1; i<ramp.count; ++i) ramp.stops[i-1]=ramp.stops[i];
                --ramp.count;
            } else sort(ramp);
            state.selected=-1;
        }
    }
    if (e.type==EventType::single || e.type==EventType::multiple) {
        state.armed=-1;
        for (int i=0;i<4;++i)
            if ((i!=1 || clipboard.available) && buttons[i].contains(e.x,e.y)) state.armed=i;
    } else if (e.type==EventType::release) {
        int b=state.armed; state.armed=-1;
        if (b>=0 && buttons[b].contains(e.x,e.y)) {
            if (b==0) { clipboard.data=ramp; clipboard.available=true; }
            if (b==1 && clipboard.available) ramp=clipboard.data;
            if (b==2) randomize(ramp,rng);
            if (b==3) flip(ramp);
        }
    }
    return {};
}
template<class Ramp> void picker_result(Ramp& ramp, State& state, int index, bool cancelled, Color c) {
    if (cancelled) state.selected=-1;
    else if (index>=0 && static_cast<unsigned>(index)<ramp.count) set_color(ramp.stops[index],c);
}
// Commands carry local coordinates. The host adapter owns suite resources.
enum class DrawKind { antialias, fill, frame, line, text };
struct DrawCommand { DrawKind kind; float x,y,w,h; Color color; const char16_t* text=nullptr; float font=11.0f; };
struct Theme { Color frame, fill, text, black; };
inline Color scaled(Color c, float factor) { c.red*=factor;c.green*=factor;c.blue*=factor;return c; }
inline void rect(std::vector<DrawCommand>& out, DrawKind kind, Rect r, Color c) {
    out.push_back({kind,float(r.left),float(r.top),float(r.right-r.left),float(r.bottom-r.top),c});
}
template<class Ramp> std::vector<DrawCommand> draw(const Ramp& ramp, const State& state,
                                                  bool can_paste, Theme theme) {
    std::vector<DrawCommand> out;
    out.push_back({DrawKind::antialias,0,0,0,0,{}});
    if (!ramp.count) rect(out,DrawKind::fill,strip,theme.black);
    else for(int x=10;x<=202;++x)
        out.push_back({DrawKind::line,float(x),5,0,50,sample(ramp,float(x-10)/192.0f)});
    rect(out,DrawKind::frame,strip,theme.frame);
    for(int i=1;i<=3;++i) {
        out.push_back({DrawKind::line,float(10+48*i),5,0,5,theme.frame});
        out.push_back({DrawKind::line,float(10+48*i),55,0,-5,theme.frame});
    }
    for(unsigned i=0;i<ramp.count;++i) {
        rect(out,DrawKind::fill,marker(ramp,i),color(ramp.stops[i]));
        rect(out,DrawKind::frame,marker(ramp,i),theme.frame);
    }
    // Container draw order: randomize, flip, copy, paste, presets.
    for(int b : {2,3,0,1}) {
        const bool enabled=b!=1 || can_paste;
        const bool hover=buttons[b].contains(state.hover_x,state.hover_y);
        float text_factor=0.3f, fill_factor=0.3f;
        if(enabled) {
            text_factor=state.armed==b ? 1.0f : 0.7f;
            fill_factor=(state.armed==b || hover) ? 1.0f : 0.7f;
        }
        out.push_back({DrawKind::antialias,0,0,0,0,{}});
        rect(out,DrawKind::fill,buttons[b],scaled(theme.fill,fill_factor));
        rect(out,DrawKind::frame,buttons[b],theme.frame);
        const auto r=buttons[b];
        out.push_back({DrawKind::text,float(r.left+r.right)*0.5f,float(r.top)+2.0f+16.0f*0.8f,
                       float(r.right-r.left),0,scaled(theme.text,text_factor),captions[b],16.0f});
    }
    return out;
}
} // namespace olm::kirakira::editor
