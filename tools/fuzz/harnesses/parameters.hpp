// Public PF_ParamDef wire units used by the existing replay helpers.
#include <fstream>
#include <sstream>
#include <string>
#include <cmath>
static bool fuzz_parameters(const char *path, PF_ParamDef *defs, int count) {
    std::ifstream file(path); if(!file)return false;
    std::string line;
    while(std::getline(file,line)) {
        std::istringstream row(line); int slot; char kind; double v,z;
        if(!(row>>slot>>kind>>v)||slot<=0||slot>=count)return false;
        auto &p=defs[slot];
        if(kind=='c') {
            int r,g,b; if(!(row>>r>>g>>b))return false;
            p.param_type=PF_Param_COLOR;
            p.u.cd.value={(A_u_char)v,(A_u_char)r,(A_u_char)g,(A_u_char)b};
        } else if(kind=='p') {
            if(!(row>>z))return false;
            p.u.td.x_value=(PF_Fixed)llround(v*65536);p.u.td.y_value=(PF_Fixed)llround(z*65536);
        } else if(kind=='a')p.u.ad.value=(PF_Fixed)llround(v*65536);
        else if(kind=='f')p.u.fd.value=(PF_Fixed)llround(v*65536);
        else if(kind=='s')p.u.fs_d.value=v;
        else if(kind=='i')p.u.sd.value=(A_long)v;
        else if(kind=='u')p.u.pd.value=(A_long)v;
        else if(kind=='b')p.u.bd.value=v!=0;
        else return false;
    }
    return true;
}
