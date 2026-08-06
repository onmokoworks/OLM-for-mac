#include "AEConfig.h"
#include "AE_EffectVers.h"

#ifndef AE_OS_WIN
	#include <AE_General.r>
#endif

resource 'PiPL' (16000) {
	{
		Kind { AEEffect },
		Name { "OLM Kira Kira" },
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
		AE_Effect_Version { 1638400 /* PF_VERSION(3, 2, 0, PF_Stage_DEVELOP, 0) = 0x190000 */ },
		AE_Effect_Info_Flags { 0 },
		AE_Effect_Global_OutFlags { 0x02008040 },
		AE_Effect_Global_OutFlags_2 { 0x08001400 },
		AE_Effect_Match_Name { "OLM OLM Kira Kira" },
		AE_Reserved_Info { 0 },
		AE_Effect_Support_URL { "https://olm.co.jp/" }
	}
};
