#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"

#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <limits>
#include <vector>

namespace {
constexpr long W = 17, H = 11;
std::vector<float> read_field(const char *path) {
	std::ifstream stream(path, std::ios::binary);
	std::vector<std::uint8_t> bytes{std::istreambuf_iterator<char>(stream), {}};
	if (bytes.size() != static_cast<std::size_t>(W * H * sizeof(float))) return {};
	std::vector<float> field(W * H); std::memcpy(field.data(), bytes.data(), bytes.size()); return field;
}
bool write_field(const char *path, const std::vector<float> &field) {
	std::ofstream stream(path, std::ios::binary);
	stream.write(reinterpret_cast<const char *>(field.data()), static_cast<std::streamsize>(field.size()*sizeof(float)));
	return static_cast<bool>(stream);
}
// Exact superseded portable body, retained only as a 37-word counterfactual.
void legacy_portable_counterfactual(float *mat, long w, long h) {
	std::vector<float> source(mat, mat + static_cast<std::size_t>(w*h));
	float minimum=source[0], maximum=source[0]; for(float v:source){minimum=std::min(minimum,v);maximum=std::max(maximum,v);}
	if(std::fabs(maximum-minimum)<std::numeric_limits<float>::epsilon())return;
	constexpr int bins=1<<12; const float scale=static_cast<float>(bins)/(maximum-minimum);
	std::array<float,bins+2> lut{}; float last=1.0f;
	for(int i=0;i<bins+2;++i)if(last>0.0f){const double v=static_cast<double>(i)/scale;lut[i]=static_cast<float>(std::exp(v*v*-0.5));last=lut[i];}
	const float spatial=static_cast<float>(std::exp(-0.5)); const long vector_width=(w/4)*4;
	for(long y=0;y<h;++y)for(long x=0;x<w;++x){
		const long top=std::max(0L,y-1),bottom=std::min(h-1,y+1),left=std::max(0L,x-1),right=std::min(w-1,x+1);
		const float center=source[y*w+x]; const float values[4]={source[top*w+x],source[y*w+left],source[y*w+right],source[bottom*w+x]}; float weights[4];
		for(int k=0;k<4;++k){float alpha=std::fabs(values[k]-center)*scale;const int index=static_cast<int>(alpha);alpha-=static_cast<float>(index);weights[k]=spatial*std::fma(lut[index+1],alpha,lut[index]*(1.0f-alpha));}
		float sum,weight_sum;if(x<vector_width){sum=weight_sum=0.0f;for(int k=0;k<4;++k){weight_sum+=weights[k];sum=std::fma(values[k],weights[k],sum);}}
		else{weight_sum=(weights[0]+weights[1])+(weights[2]+weights[3]);const float p0=values[0]*weights[0],p1=values[1]*weights[1],p2=values[2]*weights[2],p3=values[3]*weights[3];sum=(p0+p1)+(p2+p3);}
		mat[y*w+x]=(sum+center)/(weight_sum+1.0f);
	}
}
void op_order_counterfactual(float *mat,long w,long h){
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
	std::vector<float> source(mat,mat+w*h);const float spatial=::expf(-0.5f);
	for(long y=0;y<h;++y)for(long x=0;x<w;++x){const long t=std::max(0L,y-1),b=std::min(h-1,y+1),l=std::max(0L,x-1),r=std::min(w-1,x+1);const float c=source[y*w+x];const float v[4]={source[y*w+l],source[y*w+r],source[t*w+x],source[b*w+x]};float sum=0.0f,ws=0.0f;for(int k=0;k<4;++k){const float d=v[k]-c,q=d*d,wgt=::expf(-0.5f*q);ws+=wgt;sum+=bilateral_noncontracting_product(v[k],wgt);}ws=bilateral_noncontracting_product(ws,spatial);sum=bilateral_noncontracting_product(sum,spatial);mat[y*w+x]=(sum+c)/(ws+1.0f);}
}
}
int main(int argc,char **argv){if(argc!=5)return 2;auto canonical=read_field(argv[1]);if(canonical.size()!=187)return 3;auto legacy=canonical,wrong=canonical;bilateral_blur_opencv455_f32x4(canonical.data(),W,H);legacy_portable_counterfactual(legacy.data(),W,H);op_order_counterfactual(wrong.data(),W,H);return write_field(argv[2],canonical)&&write_field(argv[3],legacy)&&write_field(argv[4],wrong)?0:4;}
