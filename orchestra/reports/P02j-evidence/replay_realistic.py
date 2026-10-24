#!/usr/bin/env python3
"""Replay the explicitly Smart-only P02j corpus using the standard runner."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/fuzz'))
from adapters.olmdirectionalblur import Adapter
Adapter.routes=('smart',)
from run import main
raise SystemExit(main())
