// Configuration fields supported by the retained Smoother/Distance SDK shims.
#include <fstream>
#include <sstream>
#include <string>
static bool fuzz_parameters(const char *path, PF_ParamDef *defs, int count) {
    std::ifstream file(path);if(!file)return false;std::string line;
    while(std::getline(file,line)) {
        std::istringstream row(line);int slot;char kind;double v;
        if(!(row>>slot>>kind>>v)||slot<=0||slot>=count)return false;
        if(kind=='c') {
            int r,g,b;if(!(row>>r>>g>>b))return false;
            defs[slot].u.cd.value={(unsigned char)v,(unsigned char)r,(unsigned char)g,(unsigned char)b};
        } else if(kind=='i')defs[slot].u.sd.value=(A_long)v;
        else if(kind=='u')defs[slot].u.pd.value=(A_long)v;
        else if(kind=='b')defs[slot].u.bd.value=(A_long)v;
        else if(kind=='s')defs[slot].u.fs_d.value=v;
        else return false;
    }
    return true;
}
