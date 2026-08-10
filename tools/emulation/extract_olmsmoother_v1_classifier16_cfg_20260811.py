#!/usr/bin/env python3
"""Extract the complete PF16 classifier CFG from the pinned Smoother AEX."""
from extract_olmsmoother_v1_pf16_control_cfg_20260806 import extract

if __name__=='__main__':
    extract(0x180006A90,0x18000805B,'olmsmoother_v1_classifier16_cfg_20260811.json')
