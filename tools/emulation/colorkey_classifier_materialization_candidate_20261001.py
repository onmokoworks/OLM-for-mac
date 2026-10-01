"""Temporary native PF8 normalization, premultiplication and HSV unordered predicate."""
from colorkey_rgb_hsv_candidate_20261001 import candidate_source as comparison_source

def candidate_source(body):
    body=comparison_source(body)
    for channel,member in (('r','red'),('g','green'),('b','blue'),('a','alpha')):
        old=f'static float {channel}(const PF_Pixel8 &p) {{ return (float)p.{member} / 255.0f; }}'
        new=f'static float {channel}(const PF_Pixel8 &p) {{ return (float)p.{member} * 0.003921568859368563f; }}'
        assert body.count(old)==1;body=body.replace(old,new)
    old="""float premultiplied = value * alpha;
				if (!OLMCKPixelTraits<PixelT>::is_32bpc()) {
					const float maximum = OLMCKPixelTraits<PixelT>::max_chan();
					premultiplied = std::floor(premultiplied * maximum + 0.5f) / maximum;
				}
				return premultiplied;"""
    assert body.count(old)==1;body=body.replace(old,'return value * alpha;')
    old="""hit = (sh - key[0]) <= (float)(key_epsilon + (float)tr)
						    && std::fabs(cmp[1] - key[1]) <= (float)(key_epsilon + (float)tg)
						    && std::fabs(cmp[2] - key[2]) <= (float)(key_epsilon + (float)tb);"""
    new="""hit = !((sh - key[0]) > (float)(key_epsilon + (float)tr))
						    && !(std::fabs(cmp[1] - key[1]) > (float)(key_epsilon + (float)tg))
						    && !(std::fabs(cmp[2] - key[2]) > (float)(key_epsilon + (float)tb));"""
    assert body.count(old)==1;return body.replace(old,new)
