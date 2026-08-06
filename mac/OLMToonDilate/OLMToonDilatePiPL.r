#include "AEConfig.h"
#include "AE_EffectVers.h"

#ifndef AE_OS_WIN
	#include <AE_General.r>
#endif

resource 'PiPL' (16000) {
	{
		Kind { AEEffect },
		Name { "OLM Toon Dilate" },
		Category { "OLM Plug-ins" },
#ifdef AE_OS_WIN
	#ifdef AE_PROC_INTELx64
		CodeWin64X86 {"EffectMain"},
	#endif
#else
	#ifdef AE_OS_MAC
		CodeMacIntel64 {"EffectMain"},
		CodeMacARM64 {"EffectMain"},
	#endif
#endif
		AE_PiPL_Version { 2, 0 },
		AE_Effect_Spec_Version { PF_PLUG_IN_VERSION, PF_PLUG_IN_SUBVERS },
		AE_Effect_Version { 559104 /* PF_VERSION(1, 1, 1, PF_Stage_DEVELOP, 0) = 0x88800 */ },
		AE_Effect_Info_Flags { 0 },
		AE_Effect_Global_OutFlags { 0x02000044 },
		AE_Effect_Global_OutFlags_2 { 0x08021400 },
		AE_Effect_Match_Name { "ADBE OLMToonDilate" },
		AE_Reserved_Info { 0 },
		AE_Effect_Support_URL { "https://olm.co.jp/" }
	}
};
