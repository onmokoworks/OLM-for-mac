#include "../RampEditor.h"
#include <cassert>
#include <cstring>
#include <iostream>
using namespace olm::kirakira::editor;
struct Stop { float position,alpha,red,green,blue; };
struct Ramp { std::uint32_t count; Stop stops[16]; };
static_assert(sizeof(Ramp)==0x144);
int main() {
    Ramp r{3,{{0,1,1,0,0},{0.5f,0.25f,0,1,0},{1,0.75f,0,0,1}}};
    State s; Clipboard<Ramp> clip; std::uint32_t rng=0x810cd;
    auto event=[&](EventType t,int x,int y) { return dispatch(r,s,clip,rng,{t,x,y}); };
    assert(hit(r,5,60)==0 && hit(r,15,70)==0 && hit(r,4,65)==-1);
    assert(hit(r,16,65)==-1 && hit(r,10,59)==-1 && hit(r,10,71)==-1);
    event(EventType::single,50,65); assert(s.selected==-1);
    event(EventType::single,58,20); assert(r.count==4 && r.stops[1].position==0.25f);
    assert(r.stops[1].red==0.5f && r.stops[1].green==0.5f && r.stops[1].alpha==0.625f);
    assert(s.selected==-1);
    event(EventType::single,10,65); assert(s.selected==0);
    event(EventType::drag,500,75); assert(r.stops[0].position==1 && r.stops[0].alpha==1);
    event(EventType::drag,-50,76); assert(r.stops[0].position==0 && r.stops[0].alpha==0.5f);
    event(EventType::drag,150,75); assert(r.stops[0].alpha==1);
    const float p=r.stops[0].position;
    event(EventType::release,202,75); assert(s.selected==-1 && r.stops[2].position==p);
    event(EventType::single,202,65); event(EventType::release,202,76); assert(r.count==3);
    auto req=event(EventType::multiple,58,65); assert(req.picker==0);
    Ramp saved=r; picker_result(r,s,req.picker,true,{1,1,1,1}); assert(!std::memcmp(&saved,&r,sizeof(r)) && s.selected==-1);
    picker_result(r,s,req.picker,false,{0.2f,0.3f,0.4f,0.6f}); assert(r.stops[0].alpha==0.6f && r.stops[0].red==0.2f);
    event(EventType::single,250,40); assert(!clip.available);
    event(EventType::drag,0,0); event(EventType::release,250,40); assert(clip.available);
    Ramp other{}; State other_s; dispatch(other,other_s,clip,rng,{EventType::single,250,65});
    dispatch(other,other_s,clip,rng,{EventType::release,250,65}); assert(!std::memcmp(&other,&r,sizeof(r)));
    Clipboard<Ramp> separate; Ramp empty{};
    dispatch(empty,other_s,separate,rng,{EventType::single,250,65});
    dispatch(empty,other_s,separate,rng,{EventType::release,250,65}); assert(empty.count==0);
    saved=r; event(EventType::single,150,90);event(EventType::release,0,0); assert(!std::memcmp(&saved,&r,sizeof(r)));
    event(EventType::single,150,90);event(EventType::release,150,90);
    assert(r.stops[0].position==saved.stops[0].position && r.stops[0].alpha==saved.stops[2].alpha);
    assert(r.stops[0].red==saved.stops[2].red); flip(r); assert(!std::memcmp(&saved,&r,sizeof(r)));
    auto before_rng=rng;event(EventType::single,50,90);event(EventType::release,50,90);
    assert(rng!=before_rng && r.count==saved.count);
    for(unsigned i=0;i<r.count;++i) assert(r.stops[i].alpha==saved.stops[i].alpha && r.stops[i].position==saved.stops[i].position);
    saved=r;before_rng=rng;randomize(r,rng); assert(rng!=before_rng && std::memcmp(&saved,&r,sizeof(r)));
    auto before_hover=r;event(EventType::hover,250,40);assert(s.hover_x==250 && !std::memcmp(&r,&before_hover,sizeof(r)));
    r={};event(EventType::single,10,5);assert(r.count==1 && r.stops[0].alpha==1 && r.stops[0].red==0);
    for(int i=0;i<15;++i) event(EventType::single,202,55);
    assert(r.count==16);saved=r;event(EventType::single,100,25);assert(!std::memcmp(&r,&saved,sizeof(r)));
    assert(hit(r,202,65)==15);
    const Theme theme{{0.1f,0.2f,0.3f,1},{0.2f,0.3f,0.4f,1},{1,1,1,1},{0,0,0,1}};
    auto commands=draw(r,s,true,theme);
    assert(commands[0].kind==DrawKind::antialias);
    for(int i=0;i<193;++i) {
        const auto& c=commands[1+i]; assert(c.kind==DrawKind::line && c.x==10+i && c.y==5 && c.w==0 && c.h==50);
    }
    assert(commands[194].kind==DrawKind::frame);
    assert(commands[201].kind==DrawKind::fill && commands[201].w==10 && commands[201].h==10);
    unsigned text_count=0;for(const auto& c:commands) if(c.kind==DrawKind::text) ++text_count;
    assert(text_count==5);
    // Header toggles; seven visible previews, inclusive hit boxes, release gating.
    event(EventType::single,260,15); assert(s.menu_open);
    auto expanded=draw(r,s,true,theme);
    unsigned preview_lines=0;
    for(const auto& c:expanded) if(c.kind==DrawKind::line && c.x>=228) ++preview_lines;
    assert(preview_lines==7*65);
    event(EventType::single,240,35);event(EventType::release,240,35);
    auto first=preset<Ramp>(0);assert(!s.menu_open && !std::memcmp(&r,&first,sizeof(r)));
    event(EventType::single,260,15);event(EventType::single,240,35);
    event(EventType::drag,240,1000);assert(s.scroll==33);
    event(EventType::release,240,35);auto last=preset<Ramp>(33);
    assert(!s.menu_open && !std::memcmp(&r,&last,sizeof(r)));
    event(EventType::single,260,15);event(EventType::single,240,35);
    event(EventType::drag,240,-1000);assert(s.scroll==0);
    event(EventType::release,240,60);assert(s.menu_open); // different row: no selection
    event(EventType::single,260,15);assert(!s.menu_open);
    for(unsigned i=0;i<preset_count;++i) assert(preset<Ramp>(i).count<=16);
    r={3,{{0.5f,1,1,0,0},{0.5f,1,0,1,0},{0.25f,1,0,0,1}}};
    sort(r);assert(r.stops[0].blue==1 && r.stops[1].green==1 && r.stops[2].red==1);
    assert(hit(r,106,65)==2); // last overlapping marker wins
    auto sampled=sample(r,0.5f);assert(sampled.green==1 && sampled.red==0); // first equal stop samples
    r={2,{{0,0.25f,1,0,0},{0.00005f,0.75f,0,1,0}}};
    sampled=sample(r,0.000025f);assert(sampled.red==1 && sampled.alpha==0.25f); // original near-zero span branch
    std::cout << "ramp editor interaction and drawing assertions passed\n";
}
