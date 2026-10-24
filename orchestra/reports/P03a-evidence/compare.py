import numpy as np,json
from pathlib import Path
S=Path(__file__).resolve().parents[3]/'orchestra/state/P03a-distancegradation-pf32-downsample-ulp'
m=np.fromfile(S/'mask.bin',np.uint8).reshape(8,12)
e=np.repeat(np.repeat(m,8,axis=0),8,axis=1)
a=np.fromfile(S/'expanded.bin',np.uint8).reshape(64,96)
print('expanded differences',np.count_nonzero(e!=a))
y,x=np.indices(e.shape); d=np.full(e.shape,100000,dtype='int64')
for zy,zx in zip(*np.where(e==0)):d=np.minimum(d,(y-zy)**2+(x-zx)**2)
d=np.sqrt(d.astype('float32'))
ad=np.fromfile(S/'distance.bin',np.float32).reshape(64,96)
print('distance differences',np.count_nonzero(d!=ad))
r=(d[3::8,3::8]*np.float32(.5)+d[3::8,4::8]*np.float32(.5))*np.float32(.5)+(d[4::8,3::8]*np.float32(.5)+d[4::8,4::8]*np.float32(.5))*np.float32(.5)
ar=np.fromfile(S/'resized.bin',np.float32).reshape(8,12)
print('resized differences',np.count_nonzero(r!=ar))
for yy,xx in zip(*np.where(r!=ar)):print('resize',int(xx),int(yy),r[yy,xx].tobytes().hex(),ar[yy,xx].tobytes().hex(),d[yy*8+3:yy*8+5,xx*8+3:xx*8+5].tolist())
for yy,xx in list(zip(*np.where(d!=ad)))[:8]:print('distance',int(xx),int(yy),d[yy,xx].tobytes().hex(),ad[yy,xx].tobytes().hex())
sq=np.full(e.shape,100000,dtype='int64')
for zy,zx in zip(*np.where(e==0)):sq=np.minimum(sq,(y-zy)**2+(x-zx)**2)
with np.errstate(divide='ignore',invalid='ignore'):
 inv=np.float32(1)/np.sqrt(sq.astype('float32'))
 t=sq.astype('float32')*inv
 approx=(inv*t-np.float32(3))*(t*np.float32(-.5))
for yy in range(64):
 for xx in range(0,96,16):
  if np.any(sq[yy,xx:xx+16]==0):approx[yy,xx:xx+16]=d[yy,xx:xx+16]
print('Newton model differences',np.count_nonzero(approx!=ad))
rr=(ad[3::8,3::8]*np.float32(.5)+ad[3::8,4::8]*np.float32(.5))*np.float32(.5)+(ad[4::8,3::8]*np.float32(.5)+ad[4::8,4::8]*np.float32(.5))*np.float32(.5)
print('resize with original distance differences',np.count_nonzero(rr!=ar))

if (S/'core-distance.bin').exists():
 core=np.fromfile(S/'core-distance.bin',np.float32).reshape(64,96)
 print('production core distance differences',np.count_nonzero(core!=ad))
 assert core.tobytes()==ad.tobytes()
assert np.count_nonzero(approx!=ad)==0
assert np.count_nonzero(rr!=ar)==0
