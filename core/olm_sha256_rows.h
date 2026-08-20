#ifndef OLM_SHA256_ROWS_H
#define OLM_SHA256_ROWS_H

#include <stddef.h>
#include <stdint.h>
#include <string.h>

namespace olm {

class Sha256 {
public:
	Sha256() { reset(); }

	void reset()
	{
		state_[0] = 0x6a09e667u; state_[1] = 0xbb67ae85u;
		state_[2] = 0x3c6ef372u; state_[3] = 0xa54ff53au;
		state_[4] = 0x510e527fu; state_[5] = 0x9b05688cu;
		state_[6] = 0x1f83d9abu; state_[7] = 0x5be0cd19u;
		bytes_ = 0;
		used_ = 0;
	}

	void update(const void *data, size_t size)
	{
		const uint8_t *src = static_cast<const uint8_t *>(data);
		bytes_ += static_cast<uint64_t>(size);
		while (size) {
			const size_t take = size < 64 - used_ ? size : 64 - used_;
			memcpy(block_ + used_, src, take);
			used_ += take;
			src += take;
			size -= take;
			if (used_ == 64) {
				transform(block_);
				used_ = 0;
			}
		}
	}

	void final(uint8_t digest[32])
	{
		const uint64_t bits = bytes_ * 8u;
		block_[used_++] = 0x80;
		if (used_ > 56) {
			memset(block_ + used_, 0, 64 - used_);
			transform(block_);
			used_ = 0;
		}
		memset(block_ + used_, 0, 56 - used_);
		for (int i = 0; i < 8; ++i) {
			block_[63 - i] = static_cast<uint8_t>(bits >> (i * 8));
		}
		transform(block_);
		for (int i = 0; i < 8; ++i) {
			digest[i * 4 + 0] = static_cast<uint8_t>(state_[i] >> 24);
			digest[i * 4 + 1] = static_cast<uint8_t>(state_[i] >> 16);
			digest[i * 4 + 2] = static_cast<uint8_t>(state_[i] >> 8);
			digest[i * 4 + 3] = static_cast<uint8_t>(state_[i]);
		}
	}

private:
	static uint32_t rotate_right(uint32_t value, unsigned count)
	{
		return (value >> count) | (value << (32 - count));
	}

	void transform(const uint8_t block[64])
	{
		static const uint32_t constants[64] = {
			0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,0x923f82a4u,0xab1c5ed5u,
			0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,
			0xe49b69c1u,0xefbe4786u,0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
			0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,0x06ca6351u,0x14292967u,
			0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,
			0xa2bfe8a1u,0xa81a664bu,0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
			0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,0x5b9cca4fu,0x682e6ff3u,
			0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u
		};
		uint32_t words[64];
		for (int i = 0; i < 16; ++i) {
			words[i] = (static_cast<uint32_t>(block[i * 4]) << 24) |
			           (static_cast<uint32_t>(block[i * 4 + 1]) << 16) |
			           (static_cast<uint32_t>(block[i * 4 + 2]) << 8) |
			            static_cast<uint32_t>(block[i * 4 + 3]);
		}
		for (int i = 16; i < 64; ++i) {
			const uint32_t s0 = rotate_right(words[i - 15], 7) ^ rotate_right(words[i - 15], 18) ^ (words[i - 15] >> 3);
			const uint32_t s1 = rotate_right(words[i - 2], 17) ^ rotate_right(words[i - 2], 19) ^ (words[i - 2] >> 10);
			words[i] = words[i - 16] + s0 + words[i - 7] + s1;
		}
		uint32_t a=state_[0],b=state_[1],c=state_[2],d=state_[3];
		uint32_t e=state_[4],f=state_[5],g=state_[6],h=state_[7];
		for (int i = 0; i < 64; ++i) {
			const uint32_t s1 = rotate_right(e, 6) ^ rotate_right(e, 11) ^ rotate_right(e, 25);
			const uint32_t choice = (e & f) ^ (~e & g);
			const uint32_t t1 = h + s1 + choice + constants[i] + words[i];
			const uint32_t s0 = rotate_right(a, 2) ^ rotate_right(a, 13) ^ rotate_right(a, 22);
			const uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
			const uint32_t t2 = s0 + majority;
			h=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
		}
		state_[0]+=a; state_[1]+=b; state_[2]+=c; state_[3]+=d;
		state_[4]+=e; state_[5]+=f; state_[6]+=g; state_[7]+=h;
	}

	uint32_t state_[8];
	uint64_t bytes_;
	uint8_t block_[64];
	size_t used_;
};

inline bool sha256_active_rows_match(const void *data, size_t rowbytes,
	                                  size_t active_bytes, size_t height,
	                                  const uint8_t expected[32])
{
	if (!data || active_bytes > rowbytes) return false;
	Sha256 hash;
	const uint8_t *row = static_cast<const uint8_t *>(data);
	for (size_t y = 0; y < height; ++y) {
		hash.update(row, active_bytes);
		if (y + 1 < height) row += rowbytes;
	}
	uint8_t actual[32];
	hash.final(actual);
	uint8_t difference = 0;
	for (size_t i = 0; i < 32; ++i) difference |= actual[i] ^ expected[i];
	return difference == 0;
}

inline bool sha256_active_rows_match_hex(const void *data, size_t rowbytes,
	                                      size_t active_bytes, size_t height,
	                                      const char expected_hex[65])
{
	uint8_t expected[32];
	for (size_t i = 0; i < 32; ++i) {
		const char hi = expected_hex[i * 2];
		const char lo = expected_hex[i * 2 + 1];
		const int high = hi >= '0' && hi <= '9' ? hi - '0' :
		                 hi >= 'a' && hi <= 'f' ? hi - 'a' + 10 : -1;
		const int low = lo >= '0' && lo <= '9' ? lo - '0' :
		                lo >= 'a' && lo <= 'f' ? lo - 'a' + 10 : -1;
		if (high < 0 || low < 0) return false;
		expected[i] = static_cast<uint8_t>((high << 4) | low);
	}
	return expected_hex[64] == '\0' &&
	       sha256_active_rows_match(data, rowbytes, active_bytes, height, expected);
}

} // namespace olm

#endif
