// Reduced-world ABI support for source-included harnesses only.
static bool DirectionalWorldHasZeroOrigin(const void *, long)
{
	return true;
}

template <typename World>
static auto DirectionalTestPixelFormat(const World *world, int)
	-> decltype(world->bitdepth, PF_PixelFormat())
{
	return world->bitdepth == 8 ? PF_PixelFormat_ARGB32 :
		(world->bitdepth == 16 ? PF_PixelFormat_ARGB64 :
		 (world->bitdepth == 32 ? PF_PixelFormat_ARGB128 : PF_PixelFormat_INVALID));
}

static PF_PixelFormat DirectionalTestPixelFormat(const void *, long)
{
	return PF_PixelFormat_INVALID;
}
