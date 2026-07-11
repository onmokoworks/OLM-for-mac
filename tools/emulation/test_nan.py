import numpy as np
import cv2

src = np.array([[np.nan]], dtype=np.float32)
ret, dst1 = cv2.threshold(src, 0.5, 1.0, cv2.THRESH_BINARY_INV)
print(f"cv2 BINARY_INV NaN: {dst1[0,0]}")

dst_np1 = np.where(src <= 0.5, 0.0, 1.0).astype(np.float32)
print(f"np.where(<=) BINARY_INV NaN: {dst_np1[0,0]}")

dst_np2 = np.where(src > 0.5, 0.0, 1.0).astype(np.float32)
print(f"np.where(>) BINARY_INV NaN: {dst_np2[0,0]}")

