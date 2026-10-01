#!/usr/bin/env python3
"""Independent mixed-alpha column for the shared Thin/Blur workspace."""
import probe_olmcolorkey_around_range_20261001 as around
if __name__=='__main__':
    definition={'id':'column13_mixed_zero','width':1,'height':13,'alpha':'mixed'}
    around.thin_owner.general.FIXTURES=(definition,definition,definition)
    around.main()
