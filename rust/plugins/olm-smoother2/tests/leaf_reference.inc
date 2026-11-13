// @generated names only; function implementations are the unchanged C++ includes.

extern "C" int sm2_ref_leaf(int id, FPix *pixels, const uint8_t *classes, int w, int h, int x, int y, float smooth, float extra, const int *desc, float scale, PolyVertex *out, int *count) {
FPlane plane{pixels,(size_t)w*sizeof(FPix),0}; SmootherPolygon p{}; p.plane=&plane; p.cplane_base=classes; p.cplane_w=w; p.cplane_h=h; p.cplane_stride=w*4; p.cur_x=x; p.cur_y=y; p.smoothness_n=smooth; p.extra_n=extra; bool result=false; switch(id) {
case 0: result=win_leaf_f4a0(p,desc); break;
case 1: result=win_leaf_ec40(p,desc); break;
case 2: result=win_leaf_f7b0(p,desc); break;
case 3: result=win_leaf_f360(p,desc); break;
case 4: result=win_leaf_f220(p,desc,scale); break;
case 5: result=win_leaf_f0e0(p,desc,scale); break;
case 6: result=win_leaf_f600(p,desc); break;
case 7: result=win_leaf_e640(p,desc); break;
case 8: result=win_leaf_f450(p,desc); break;
case 9: result=win_leaf_ead0(p,desc); break;
case 10: result=win_leaf_f740(p,desc); break;
case 11: result=win_leaf_f310(p,desc); break;
case 12: result=win_leaf_f1d0(p,desc,scale); break;
case 13: result=win_leaf_f090(p,desc,scale); break;
case 14: result=win_leaf_f590(p,desc); break;
case 15: result=win_leaf_e4b0(p,desc); break;
case 16: result=win_leaf_f4f0(p,desc); break;
case 17: result=win_leaf_edb0(p,desc); break;
case 18: result=win_leaf_f820(p,desc); break;
case 19: result=win_leaf_f3b0(p,desc); break;
case 20: result=win_leaf_f270(p,desc,scale); break;
case 21: result=win_leaf_f130(p,desc,scale); break;
case 22: result=win_leaf_f670(p,desc); break;
case 23: result=win_leaf_e7c0(p,desc); break;
case 24: result=win_leaf_f540(p,desc); break;
case 25: result=win_leaf_ef20(p,desc); break;
case 26: result=win_leaf_f890(p,desc); break;
case 27: result=win_leaf_f400(p,desc); break;
case 28: result=win_leaf_f2c0(p,desc,scale); break;
case 29: result=win_leaf_f180(p,desc,scale); break;
case 30: result=win_leaf_f6e0(p,desc); break;
case 31: result=win_leaf_e950(p,desc); break;
default: return -1; } *count=p.count; std::memcpy(out,p.samples,p.count*sizeof(PolyVertex)); return result; }