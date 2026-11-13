//! Pinned bindgen Mac enum constants are unsigned, although the SDK uses
//! signed A_long typedefs for PF_Cmd/PF_PixelFormat. Normalize only constants;
//! retain every SDK structure, callback and ABI type from the pinned crate.
pub use after_effects::sys::*;

macro_rules! signed_constants {
    ($ty:ty; $($name:ident),+ $(,)?) => {
        $(pub const $name: $ty = after_effects::sys::$name as $ty;)+
    };
}
signed_constants!(PF_Cmd;
    PF_Cmd_ABOUT, PF_Cmd_GLOBAL_SETUP, PF_Cmd_UNUSED_0, PF_Cmd_GLOBAL_SETDOWN,
    PF_Cmd_PARAMS_SETUP, PF_Cmd_SEQUENCE_SETUP, PF_Cmd_SEQUENCE_RESETUP,
    PF_Cmd_SEQUENCE_FLATTEN, PF_Cmd_SEQUENCE_SETDOWN, PF_Cmd_DO_DIALOG,
    PF_Cmd_FRAME_SETUP, PF_Cmd_RENDER, PF_Cmd_FRAME_SETDOWN,
    PF_Cmd_USER_CHANGED_PARAM, PF_Cmd_UPDATE_PARAMS_UI, PF_Cmd_EVENT,
    PF_Cmd_GET_EXTERNAL_DEPENDENCIES, PF_Cmd_COMPLETELY_GENERAL,
    PF_Cmd_QUERY_DYNAMIC_FLAGS, PF_Cmd_AUDIO_RENDER, PF_Cmd_AUDIO_SETUP,
    PF_Cmd_AUDIO_SETDOWN, PF_Cmd_ARBITRARY_CALLBACK, PF_Cmd_SMART_PRE_RENDER,
    PF_Cmd_SMART_RENDER, PF_Cmd_RESERVED1, PF_Cmd_RESERVED2, PF_Cmd_RESERVED3,
    PF_Cmd_GET_FLATTENED_SEQUENCE_DATA, PF_Cmd_TRANSLATE_PARAMS_TO_PREFS,
    PF_Cmd_RESERVED4, PF_Cmd_SMART_RENDER_GPU, PF_Cmd_GPU_DEVICE_SETUP,
    PF_Cmd_GPU_DEVICE_SETDOWN, PF_Cmd_NUM_CMDS,
);
signed_constants!(PF_PixelFormat;
    PF_PixelFormat_ARGB32, PF_PixelFormat_ARGB64, PF_PixelFormat_ARGB128,
    PF_PixelFormat_GPU_BGRA128, PF_PixelFormat_RESERVED, PF_PixelFormat_BGRA32,
    PF_PixelFormat_VUYA32, PF_PixelFormat_NTSCDV25, PF_PixelFormat_PALDV25,
    PF_PixelFormat_INVALID,
);
signed_constants!(PF_FunctionSelector;
    PF_Arbitrary_NEW_FUNC, PF_Arbitrary_DISPOSE_FUNC, PF_Arbitrary_COPY_FUNC,
    PF_Arbitrary_FLAT_SIZE_FUNC, PF_Arbitrary_FLATTEN_FUNC,
    PF_Arbitrary_UNFLATTEN_FUNC, PF_Arbitrary_INTERP_FUNC,
    PF_Arbitrary_COMPARE_FUNC, PF_Arbitrary_PRINT_SIZE_FUNC,
    PF_Arbitrary_PRINT_FUNC, PF_Arbitrary_SCAN_FUNC,
);
signed_constants!(PF_ArbCompareResult;
    PF_ArbCompare_EQUAL, PF_ArbCompare_LESS, PF_ArbCompare_MORE, PF_ArbCompare_NOT_EQUAL,
);
signed_constants!(PF_ParamUIFlags;
    PF_PUI_NONE, PF_PUI_TOPIC, PF_PUI_CONTROL, PF_PUI_STD_CONTROL_ONLY,
    PF_PUI_NO_ECW_UI, PF_PUI_ECW_SEPARATOR, PF_PUI_DISABLED,
    PF_PUI_DONT_ERASE_TOPIC, PF_PUI_DONT_ERASE_CONTROL, PF_PUI_RADIO_BUTTON,
    PF_PUI_INVISIBLE, PF_PUI_RESERVED,
);
signed_constants!(PF_CustomEventFlags;
    PF_CustomEFlag_NONE, PF_CustomEFlag_COMP, PF_CustomEFlag_LAYER,
    PF_CustomEFlag_EFFECT, PF_CustomEFlag_PREVIEW,
);
signed_constants!(PF_EffectArea; PF_EA_NONE, PF_EA_PARAM_TITLE, PF_EA_CONTROL);
signed_constants!(PF_ChangeFlags;
    PF_ChangeFlag_NONE, PF_ChangeFlag_CHANGED_VALUE, PF_ChangeFlag_RESERVED,
    PF_ChangeFlag_SET_TO_VARY, PF_ChangeFlag_SET_TO_CONSTANT,
);
signed_constants!(PF_EventOutFlags;
    PF_EO_NONE, PF_EO_HANDLED_EVENT, PF_EO_ALWAYS_UPDATE, PF_EO_NEVER_UPDATE,
    PF_EO_UPDATE_NOW,
);
