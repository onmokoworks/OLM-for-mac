import numpy as np
import cv2

def check(dtype, thresh, maxval, ttype):
    src = np.array([[10, 200]], dtype=dtype)
    ret, dst = cv2.threshold(src, thresh, maxval, ttype)
    print(f"[{np.dtype(dtype).name}] thr={thresh} max={maxval} type={ttype} => dst={dst[0].tolist()}")

print("8U ithresh < 0 (-10):")
check(np.uint8, -10, 255, cv2.THRESH_BINARY)
check(np.uint8, -10, 255, cv2.THRESH_BINARY_INV)
check(np.uint8, -10, 255, cv2.THRESH_TRUNC)
check(np.uint8, -10, 255, cv2.THRESH_TOZERO)
check(np.uint8, -10, 255, cv2.THRESH_TOZERO_INV)

print("8U ithresh >= 255 (300):")
check(np.uint8, 300, 255, cv2.THRESH_BINARY)
check(np.uint8, 300, 255, cv2.THRESH_BINARY_INV)
check(np.uint8, 300, 255, cv2.THRESH_TRUNC)
check(np.uint8, 300, 255, cv2.THRESH_TOZERO)
check(np.uint8, 300, 255, cv2.THRESH_TOZERO_INV)

print("16S ithresh < -32768 (-40000):")
check(np.int16, -40000, 255, cv2.THRESH_BINARY)
check(np.int16, -40000, 255, cv2.THRESH_TRUNC)
check(np.int16, -40000, 255, cv2.THRESH_TOZERO)

print("16S ithresh >= 32767 (40000):")
check(np.int16, 40000, 255, cv2.THRESH_BINARY)
check(np.int16, 40000, 255, cv2.THRESH_TRUNC)
check(np.int16, 40000, 255, cv2.THRESH_TOZERO)

print("16U ithresh < 0 (-10):")
check(np.uint16, -10, 255, cv2.THRESH_BINARY)
check(np.uint16, -10, 255, cv2.THRESH_TRUNC)
check(np.uint16, -10, 255, cv2.THRESH_TOZERO)

print("16U ithresh >= 65535 (70000):")
check(np.uint16, 70000, 255, cv2.THRESH_BINARY)
check(np.uint16, 70000, 255, cv2.THRESH_TRUNC)
check(np.uint16, 70000, 255, cv2.THRESH_TOZERO)

