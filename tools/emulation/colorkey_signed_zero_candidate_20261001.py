"""Restore the initial typed matte's signed zero before neighborhood operations."""
def candidate_source(body):
    old='''				OLMCKPixelTraits<PixelT>::zero_alpha(*outP);
			}
			// Native replacement precedes Thin/Blur'''
    new='''				OLMCKPixelTraits<PixelT>::zero_alpha(*outP);
				// FUN_1800035d0 copies the matched source alpha verbatim.
				// Zero is not a distance seed, but its sign remains in the matte.
				// Negative Thin skips zero alpha; positive Thin copies source RGBA.
				const size_t matte_index = (size_t)y * (size_t)w + (size_t)x;
				if (OLMCKPixelTraits<PixelT>::is_32bpc() && info.color_keep &&
				    (info.edge_thin_amount != 0.0 || IsRecoveredPublicBlur(info)) &&
				    OLMCKPixelTraits<PixelT>::a(*inP) == 0.0f &&
				    (matched_index[matte_index] >= 0 || thin_expanded[matte_index]))
					OLMCKPixelTraits<PixelT>::restore_alpha(*outP, *inP);
			}
			// Native replacement precedes Thin/Blur'''
    assert body.count(old)==1
    return body.replace(old,new)
