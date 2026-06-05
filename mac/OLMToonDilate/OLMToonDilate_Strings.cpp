#include "OLMToonDilate.h"

typedef struct {
	A_u_long	index;
	A_char		str[256];
} TableString;

TableString g_strs[StrID_NUMTYPES] = {
	{ StrID_NONE,                    "" },
	{ StrID_Name,                    "OLM Toon Dilate" },
	{ StrID_Description,             "Port of OLM Toon Dilate.\rCopyright 2010 OLM Digital, Inc." },
	{ StrID_SearchRadius_Param_Name, "Search Radius" },
};

char *GetStringPtr(int strNum)
{
	return g_strs[strNum].str;
}
