import subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CPP=r'''
#include "core/dblur_generic_budget.h"
#include <limits>
using namespace olm::dblur::generic;
int main(){
 RenderEstimate neutral{},features{},rejected{};rejected.plugin_owned_live_bytes=123;
 if(!EstimateRender(37,29,32,7,11,0,&neutral))return 1;
 if(!EstimateGeneralDeepRender(37,29,32,7,11,5,7,true,true,3,1000,&features))return 2;
 if(features.plugin_owned_live_bytes<=neutral.plugin_owned_live_bytes+1000||features.operation_units<=neutral.operation_units)return 3;
 if(features.smart_staging_bytes!=1000||features.weight_bytes<=neutral.weight_bytes)return 4;
 if(EstimateGeneralDeepRender(4096,2160,32,4000,4000,100,100,true,true,1,0,&rejected)||rejected.plugin_owned_live_bytes!=123)return 5;
 if(EstimateGeneralDeepRender(37,29,32,7,11,5,7,true,true,3,std::numeric_limits<std::size_t>::max(),&rejected))return 6;
 if(EstimateGeneralDeepRender(37,29,32,7,11,101,7,true,true,3,0,&rejected))return 7;
 if(EstimateGeneralDeepRender(37,29,32,7,11,5,7,true,true,.5f,0,&rejected))return 8;
 if(EstimateGeneralDeepRender(37,29,32,7,11,5,7,true,true,std::numeric_limits<float>::quiet_NaN(),0,&rejected))return 9;
 if(EstimateGeneralDeepRender(37,29,8,7,11,5,7,true,true,3,0,&rejected))return 10;
 if(EstimateGeneralDeepRender(-1,29,32,7,11,5,7,true,true,3,0,&rejected))return 11;
 if(!EstimateGeneralDeepRender(37,29,32,7,11,0,0,false,false,0,0,&features))return 12;
 if(features.core_workspace_bytes!=neutral.core_workspace_bytes||features.operation_units!=neutral.operation_units)return 13;
 RenderEstimate layer{},layer16{};
 if(!EstimateGeneralDeepRender(37,29,32,7,11,0,0,false,false,0,0,&layer,true))return 14;
 std::uint64_t full_row_units=0;
 if(!EstimateOperationUnits(neutral.work,neutral.work.width,neutral.work.width,&full_row_units))return 20;
 if(layer.core_workspace_bytes!=neutral.core_workspace_bytes+neutral.work.pixels*8u ||
    layer.wrapper_bytes!=neutral.wrapper_bytes+37u*29u*16u ||
    layer.operation_units!=full_row_units+neutral.work.pixels*32u)return 15;
 if(layer.plugin_owned_live_bytes!=neutral.plugin_owned_live_bytes+neutral.work.pixels*8u+37u*29u*16u+8u)return 16;
 if(!EstimateGeneralDeepRender(37,29,16,7,11,0,0,false,false,0,0,&layer16,true))return 17;
 if(layer16.core_workspace_bytes!=layer.core_workspace_bytes ||
    layer16.wrapper_bytes*2u!=layer.wrapper_bytes)return 18;
 if(EstimateGeneralDeepRender(4096,2160,32,4000,4000,100,100,true,false,0,0,&rejected,true)||rejected.plugin_owned_live_bytes!=123)return 19;
 if(!EstimateGeneralDeepRender(720,480,16,7,11,0,0,false,false,0,0,&layer16,true,4.000016) ||
    EstimateGeneralDeepRender(720,480,32,7,11,0,0,false,false,0,0,&rejected,true))return 21;
 if(!EstimateGeneralDeepRender(720,480,32,7,11,0,0,false,false,0,0,&layer,true,1.000004))return 22;
 if(!EstimateGeneralDeepRender(720,480,32,7,11,0,0,false,false,0,0,&layer,true,8))return 23;
 if(EstimateGeneralDeepRender(720,480,32,7,11,0,0,false,false,0,0,&rejected,true,80))return 24;
 if(EstimateGeneralDeepRender(37,29,32,7,11,0,0,false,false,0,0,&rejected,true,-1) ||
    EstimateGeneralDeepRender(37,29,32,7,11,0,0,false,false,0,0,&rejected,true,std::numeric_limits<double>::quiet_NaN()) ||
    rejected.plugin_owned_live_bytes!=123)return 25;
 if(EstimateGeneralDeepRender(37,29,32,4001,0,0,0,false,false,0,0,&rejected,true,1))return 26;
 std::uint64_t wide_units=0;
 if(!EstimateScatterPerRow(5800,5800,&wide_units)||wide_units==0)return 27;
 if(EstimateGeneralDeepRender(720,480,16,7,11,0,0,false,false,0,0,&rejected,true))return 28;
 if(!EstimateGeneralDeepRender(37,29,16,7,11,0,0,false,false,0,0,&layer16,true,4.000016))return 29;
 if(layer16.operation_units<=neutral.operation_units+neutral.work.pixels*32u)return 30;
 if(EstimateGeneralDeepRender(37,29,16,7,11,0,0,false,false,0,0,&rejected,true,0)||rejected.plugin_owned_live_bytes!=123)return 31;
 return 0;
}
'''
class FeatureBudgetTests(unittest.TestCase):
 def test_checked_budget_and_rejection(self):
  with tempfile.TemporaryDirectory(prefix='dblur_feature_budget_') as td:
   src=Path(td)/'probe.cpp';binary=Path(td)/'probe';src.write_text(CPP)
   subprocess.run(['clang++','-std=c++17','-O2','-I',str(ROOT),str(src),'-o',str(binary)],check=True,capture_output=True)
   subprocess.run([str(binary)],check=True,capture_output=True)
if __name__=='__main__':unittest.main()
