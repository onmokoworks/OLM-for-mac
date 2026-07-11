"""
sidecar_oracle.py — Independent oracle for selected OpenCV 4.5.5 semantics.
Called via subprocess by test_opencv_detour.py.
"""

import sys
import numpy as np
import cv2

def main():
    if len(sys.argv) != 3:
        print("Usage: sidecar_oracle.py <in_npz> <out_npz>")
        sys.exit(1)
    
    in_path = sys.argv[1]
    out_path = sys.argv[2]
    
    data = np.load(in_path)
    src = data["src"]
    op = str(data["op"][0]) if "op" in data else "threshold"

    if op == "threshold":
        thresh = float(data["thresh"])
        maxval = float(data["maxval"])
        ttype = int(data["ttype"])
        retval, dst = cv2.threshold(src, thresh, maxval, ttype)
        np.savez(out_path, dst=dst, retval=np.array([retval], dtype=np.float64))
        return

    if op == "distance_transform_l2_precise":
        dst = cv2.distanceTransform(src, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
        np.savez(out_path, dst=dst.astype(np.float32, copy=False))
        return

    if op == "normalize_minmax":
        alpha = float(data["alpha"])
        beta = float(data["beta"])
        dst = cv2.normalize(src, None, alpha, beta, cv2.NORM_MINMAX)
        np.savez(out_path, dst=dst.astype(np.float32, copy=False))
        return

    raise ValueError(f"unknown op {op!r}")

if __name__ == "__main__":
    main()
