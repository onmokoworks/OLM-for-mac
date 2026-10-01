"""Temporary general recovery including SSE invalid arithmetic/conversion.

The initial owner probe remains immutable so its capture hashes stay meaningful.
"""
import probe_olmcolorkey_inside_outside_owner_20261001 as initial

def candidate_source(body):
    body=initial.candidate_source(body)
    anchor='template <typename PixelT>\nstruct OLMCKPixelTraits;'
    assert body.count(anchor)==1
    helpers='''// The AEX uses MULSS and CVTTSS2SI with masked invalid exceptions.
// Preserve its negative quiet NaN at the phase operation, before sin/writing.
static float NativeBlurPhaseProduct(float distance, float ratio)
{
	if (distance == 0.0f && std::isinf(ratio))
		return -std::numeric_limits<float>::quiet_NaN();
	return distance * ratio;
}

static int NativeBlurInt32(float value)
{
	if (!std::isfinite(value) || value < -2147483648.0f || value >= 2147483648.0f)
		return std::numeric_limits<int>::min();
	return static_cast<int>(value);
}

'''
    body=body.replace(anchor,helpers+anchor)
    old='((int)((float)dst.alpha * weight))'
    assert body.count(old)==2
    body=body.replace(old,'(NativeBlurInt32((float)dst.alpha * weight))')
    start=body.index('if (IsRecoveredPublicBlur(info) && edge_blur_direction != 2)')
    end=body.index('if (IsRecoveredPublicBlur(info))',start+1)
    fragment=body[start:end]
    assert fragment.count('(double)(native_dist * ratio)')==2
    fragment=fragment.replace('(double)(native_dist * ratio)','(double)NativeBlurPhaseProduct(native_dist, ratio)')
    return body[:start]+fragment+body[end:]
