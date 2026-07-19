# -*- coding: utf-8 -*-
"""GAS 폰트 렌더 모델 B: GBU식 플레인 인터리브.
14x14 4bpp cell(98B)에 글리프 2개: cell=idx//2, plane=idx%2 (lo=nibble&3, hi=(nibble>>2)&3).
여러 스캔/니블 순서 변형을 아틀라스로 출력."""
import numpy as np, os
from PIL import Image

OUT = r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas"
raw = open(os.path.join(OUT,"font_j14x14.bin"),"rb").read()
W=H=14
PAL=np.array([255,170,85,0],dtype=np.uint8)
CELL=98  # 2 glyph 4bpp
ncell=len(raw)//CELL

def nibbles(cell_bytes, lo_first=True):
    # 98바이트 -> 196니블 (픽셀당 1니블, 4bpp)
    out=np.zeros(W*H,dtype=np.uint8)
    for i in range(W*H):
        byte=cell_bytes[i>>1]
        if (i&1)==0:
            n = byte&0x0F if lo_first else (byte>>4)
        else:
            n = (byte>>4) if lo_first else (byte&0x0F)
        out[i]=n
    return out

def render(idx, lo_first=True, plane_lohi=True):
    cell=idx//2; plane=idx%2
    cb=raw[cell*CELL:(cell+1)*CELL]
    nib=nibbles(cb, lo_first)
    if plane_lohi:
        v = (nib & 3) if plane==0 else ((nib>>2)&3)
    else:
        v = ((nib>>2)&3) if plane==0 else (nib & 3)
    return v.reshape(H,W)

def atlas(start, lo_first=True, plane_lohi=True, cols=32, rows=24, scale=2):
    cellpx=W+2
    img=np.full((rows*cellpx*scale, cols*cellpx*scale),40,dtype=np.uint8)
    for gi in range(rows*cols):
        idx=start+gi
        if idx//2>=ncell: break
        m=render(idx, lo_first, plane_lohi); gray=PAL[m]
        big=np.kron(gray,np.ones((scale,scale),dtype=np.uint8))
        r=gi//cols; c=gi%cols
        img[r*cellpx*scale:r*cellpx*scale+H*scale, c*cellpx*scale:c*cellpx*scale+W*scale]=big
    return Image.fromarray(img,'L')

# 4가지 조합
for lo in (True,False):
    for lh in (True,False):
        tag=f"lo{int(lo)}_lh{int(lh)}"
        atlas(0,lo,lh).save(os.path.join(OUT,f"B_{tag}_0.png"))
print("모델B 아틀라스 4종 저장 (B_lo?_lh?_0.png)")
