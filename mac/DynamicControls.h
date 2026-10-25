#pragma once

// UI-only helpers. Callers pass parameter slots, never persistent disk IDs.
// Hiding a stream is independent of the parameter's PF_PUI_DISABLED flag.
static PF_Err OLMSetHidden(PF_InData *in_data, A_long index, bool hidden)
{
    PF_Err err = PF_Err_NONE;
    AEGP_SuiteHandler suites(in_data->pica_basicP);
    AEGP_EffectRefH effect = nullptr;
    AEGP_StreamRefH stream = nullptr;
    ERR(suites.PFInterfaceSuite1()->AEGP_GetNewEffectForEffect(
        0, in_data->effect_ref, &effect));
    if (!err) ERR(suites.StreamSuite2()->AEGP_GetNewEffectStreamByIndex(
        0, effect, index, &stream));
    if (!err) ERR(suites.DynamicStreamSuite3()->AEGP_SetDynamicStreamFlag(
        stream, AEGP_DynStreamFlag_HIDDEN, FALSE, hidden ? TRUE : FALSE));
    if (stream) {
        const PF_Err cleanup = suites.StreamSuite2()->AEGP_DisposeStream(stream);
        if (!err) err = cleanup;
    }
    if (effect) {
        const PF_Err cleanup = suites.EffectSuite3()->AEGP_DisposeEffect(effect);
        if (!err) err = cleanup;
    }
    return err;
}

static PF_Err OLMSetDisabled(PF_InData *in_data, PF_ParamDef *params[],
                             A_long index, bool disabled)
{
    PF_ParamDef copy = *params[index];
    if (disabled) copy.ui_flags |= PF_PUI_DISABLED;
    else copy.ui_flags &= ~PF_PUI_DISABLED;
    AEGP_SuiteHandler suites(in_data->pica_basicP);
    return suites.ParamUtilsSuite3()->PF_UpdateParamUI(in_data->effect_ref, index, &copy);
}
