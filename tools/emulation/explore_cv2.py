import numpy as np
import cv2
import math

print(f"cv2 version: {cv2.__version__}")
print(f"numpy version: {np.__version__}")

def check(dtype, thresh, maxval, ttype, src_val):
    src = np.array([[src_val]], dtype=dtype)
    try:
        ret, dst = cv2.threshold(src, thresh, maxval, ttype)
        print(f"[{np.dtype(dtype).name}] thresh={thresh} maxval={maxval} type={ttype} src={src_val} => dst={dst[0,0]} ret={ret}")
    except Exception as e:
        print(f"[{np.dtype(dtype).name}] thresh={thresh} maxval={maxval} type={ttype} src={src_val} => ERROR: {e}")

check(np.uint8, 300, 255, cv2.THRESH_BINARY, 100)
check(np.uint8, -10, 255, cv2.THRESH_BINARY, 100)
check(np.uint8, 100, 254.6, cv2.THRESH_BINARY, 200)
check(np.uint8, 100, 254.5, cv2.THRESH_BINARY, 200)
check(np.uint8, 100, 253.5, cv2.THRESH_BINARY, 200)
check(np.int16, -5.5, 255, cv2.THRESH_TRUNC, 10)
check(np.int16, -5.1, 255, cv2.THRESH_TRUNC, 10)
check(np.uint16, 70000, 255, cv2.THRESH_BINARY, 100)
check(np.uint16, -10, 255, cv2.THRESH_BINARY, 100)
check(np.float32, 0.5, 1.0, cv2.THRESH_BINARY, float('nan'))
check(np.float32, 0.5, 1.0, cv2.THRESH_BINARY_INV, float('nan'))
check(np.float32, 0.5, 1.0, cv2.THRESH_TOZERO, float('nan'))
check(np.float32, 0.5, 1.0, cv2.THRESH_TOZERO_INV, float('nan'))
check(np.float32, 0.5, 1.0, cv2.THRESH_TRUNC, float('nan'))
check(np.float32, 0.1, 1.0, cv2.THRESH_BINARY, 0.5)
