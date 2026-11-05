"""Select the original T22 pair or the T23 blur capture builds."""
import sys
T23 = '--t23' in sys.argv
TICKET = 'T23-live-world-capture-radial-dblur-blur' if T23 else 'T22-live-world-capture-dg-kirakira'
PLUGINS = ('OLMRadialBlur','OLMDirectionalBlur','OLMBlur') if T23 else ('OLMDistanceGradation','OLMKiraKira')
