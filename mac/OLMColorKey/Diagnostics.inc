// Included by OLMColorKey.cpp; preserves the single translation unit.
static PF_Err ColorKeyRefusal(const char *function, const char *tag, int line)
{
#if !defined(AE_OS_WIN)
    const int saved_errno = errno;
    const char *path = std::getenv("OLM_REFUSAL_TRACE");
    if (path && path[0]) {
        const int fd = ::open(path, O_WRONLY | O_CREAT | O_APPEND, 0666);
        if (fd >= 0) {
            char entry[384];
            const int n = std::snprintf(entry, sizeof(entry), "%s:%s@%d\n", function, tag, line);
            if (n > 0 && static_cast<size_t>(n) < sizeof(entry)) {
                const ssize_t written = ::write(fd, entry, static_cast<size_t>(n));
                (void)written;
            }
            ::close(fd);
        }
    }
    errno = saved_errno;
#endif
    return PF_Err_BAD_CALLBACK_PARAM;
}
#define OLM_COLORKEY_REFUSAL(tag) ColorKeyRefusal(__func__, tag, __LINE__)


#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <exception>
#include <limits>
#include <new>
#include <vector>

#if !defined(AE_OS_WIN)
#include <cerrno>
#include <cstdint>
#include <dlfcn.h>
#include <fcntl.h>
#include <limits.h>
#include <unistd.h>
#endif

#if !defined(AE_OS_WIN)
static PF_Err
CapturePixelFloatEntryIfRequested(const PF_EffectWorld *input_world, short bitdepth)
{
	const char *enabled = std::getenv("OLM_PF_PIXELFLOAT_ENTRY_CAPTURE");
	if (!enabled || std::strcmp(enabled, "1") != 0) return PF_Err_NONE;

	const char *dump_path = std::getenv("OLM_PF_PIXELFLOAT_ENTRY_DUMP");
	const char *metadata_path = std::getenv("OLM_PF_PIXELFLOAT_ENTRY_METADATA");
	const char *nonce = std::getenv("OLM_PF_PIXELFLOAT_ENTRY_NONCE");
	const char *case_id = std::getenv("OLM_PF_PIXELFLOAT_ENTRY_CASE");
	const char *expected_plugin_sha256 = std::getenv("OLM_PF_PIXELFLOAT_ENTRY_EXPECTED_PLUGIN_SHA256");
	if (!input_world || !input_world->data || bitdepth != 32 ||
	    !dump_path || !*dump_path || !metadata_path || !*metadata_path ||
	    !nonce || std::strlen(nonce) < 32 ||
	    !case_id || std::strcmp(case_id, "olmcolorkey__case_0002") != 0 ||
	    !expected_plugin_sha256 || std::strlen(expected_plugin_sha256) != 64 ||
	    input_world->width <= 0 || input_world->height <= 0 ||
	    input_world->rowbytes < input_world->width * (A_long)sizeof(PF_PixelFloat) ||
	    sizeof(PF_PixelFloat) != 16) {
		return PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	const uint16_t endian_probe = 1;
	if (*reinterpret_cast<const uint8_t *>(&endian_probe) != 1) {
		return PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	for (size_t i = 0; i < 64; ++i) {
		if (!((expected_plugin_sha256[i] >= '0' && expected_plugin_sha256[i] <= '9') ||
		      (expected_plugin_sha256[i] >= 'a' && expected_plugin_sha256[i] <= 'f'))) {
			return PF_Err_INTERNAL_STRUCT_DAMAGED;
		}
	}

	Dl_info image_info;
	char loaded_plugin_path[PATH_MAX];
	if (dladdr(reinterpret_cast<const void *>(&CapturePixelFloatEntryIfRequested), &image_info) == 0 ||
	    !image_info.dli_fname || !realpath(image_info.dli_fname, loaded_plugin_path) ||
	    std::strchr(loaded_plugin_path, '"') || std::strchr(loaded_plugin_path, '\\')) {
		return PF_Err_INTERNAL_STRUCT_DAMAGED;
	}

	char claim_path[4096];
	char dump_tmp[4096];
	char metadata_tmp[4096];
	const long pid = (long)getpid();
	if (std::snprintf(claim_path, sizeof(claim_path), "%s.claim", metadata_path) >= (int)sizeof(claim_path) ||
	    std::snprintf(dump_tmp, sizeof(dump_tmp), "%s.%ld.tmp", dump_path, pid) >= (int)sizeof(dump_tmp) ||
	    std::snprintf(metadata_tmp, sizeof(metadata_tmp), "%s.%ld.tmp", metadata_path, pid) >= (int)sizeof(metadata_tmp)) {
		return PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	const int claim_fd = open(claim_path, O_WRONLY | O_CREAT | O_EXCL, 0600);
	if (claim_fd < 0) return errno == EEXIST ? PF_Err_NONE : PF_Err_INTERNAL_STRUCT_DAMAGED;
	close(claim_fd);

	FILE *dump = std::fopen(dump_tmp, "wb");
	if (!dump) return PF_Err_INTERNAL_STRUCT_DAMAGED;
	bool ok = true;
	for (A_long y = 0; y < input_world->height && ok; ++y) {
		const char *row = reinterpret_cast<const char *>(input_world->data) +
		                  (size_t)y * (size_t)input_world->rowbytes;
		ok = std::fwrite(row, 1, (size_t)input_world->rowbytes, dump) == (size_t)input_world->rowbytes;
	}
	if (std::fflush(dump) != 0) ok = false;
	if (fsync(fileno(dump)) != 0) ok = false;
	if (std::fclose(dump) != 0) ok = false;
	if (!ok || std::rename(dump_tmp, dump_path) != 0) {
		std::remove(dump_tmp);
		return PF_Err_INTERNAL_STRUCT_DAMAGED;
	}

	FILE *metadata = std::fopen(metadata_tmp, "w");
	if (!metadata) return PF_Err_INTERNAL_STRUCT_DAMAGED;
	const unsigned long long byte_count =
	    (unsigned long long)(size_t)input_world->rowbytes * (unsigned long long)(size_t)input_world->height;
	std::fprintf(metadata,
		"{\n"
		"  \"kind\": \"olm_pf_pixel_float_entry_capture_provenance\",\n"
		"  \"schema\": 3,\n"
		"  \"producer\": \"OLMColorKey.plugin\",\n"
		"  \"capture_method\": \"macos-env-gated-plugin-instrumentation\",\n"
		"  \"capture_point\": \"SmartRender.after_checkout_layer_pixels.before_checkout_output\",\n"
		"  \"case\": \"olmcolorkey__case_0002\",\n"
		"  \"nonce\": \"%s\",\n"
		"  \"pid\": %ld,\n"
		"  \"loaded_plugin_executable\": \"%s\",\n"
		"  \"launch_expected_plugin_sha256\": \"%s\",\n"
		"  \"bitdepth\": %d,\n"
		"  \"pixel_type\": \"PF_PixelFloat\",\n"
		"  \"channel_order\": [\"alpha\", \"red\", \"green\", \"blue\"],\n"
		"  \"endianness\": \"little\",\n"
		"  \"pixel_stride_bytes\": %lu,\n"
		"  \"width\": %ld,\n"
		"  \"height\": %ld,\n"
		"  \"rowbytes\": %ld,\n"
		"  \"bytes\": %llu,\n"
		"  \"world_data_address\": \"%p\"\n"
		"}\n",
		nonce, pid, loaded_plugin_path, expected_plugin_sha256,
		(int)bitdepth, (unsigned long)sizeof(PF_PixelFloat),
		(long)input_world->width, (long)input_world->height, (long)input_world->rowbytes,
		byte_count, input_world->data);
	ok = std::fflush(metadata) == 0;
	if (fsync(fileno(metadata)) != 0) ok = false;
	if (std::fclose(metadata) != 0) ok = false;
	if (!ok || std::rename(metadata_tmp, metadata_path) != 0) {
		std::remove(metadata_tmp);
		return PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	return PF_Err_NONE;
}
#endif

static void UnionLRect(const PF_LRect *src, PF_LRect *dst)
{
	if (dst->left == dst->right || dst->top == dst->bottom) {
		*dst = *src;
	} else if (src->left != src->right && src->top != src->bottom) {
		if (src->left   < dst->left)   dst->left   = src->left;
		if (src->top    < dst->top)    dst->top    = src->top;
		if (src->right  > dst->right)  dst->right  = src->right;
		if (src->bottom > dst->bottom) dst->bottom = src->bottom;
	}
}

