import numpy as np
import cv2

def check(dtype, thresh, maxval, ttype):
    src = np.array([[10, 200]], dtype=dtype)
    ret, dst = cv2.threshold(src, thresh, maxval, ttype)
    print(f"[{np.dtype(dtype).name}] thr={thresh} max={maxval} type={ttype} => dst={dst[0].tolist()}")

for dtype in (np.uint8, np.int16, np.uint16):
    minv = np.iinfo(dtype).min
    maxv = np.iinfo(dtype).max
    print(f"--- {dtype.__name__} ---")
    for thr in (minv - 1000, maxv + 1000):
        for typ in range(5):
            check(dtype, thr, 255, typ)

