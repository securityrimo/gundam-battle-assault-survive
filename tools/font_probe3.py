# -*- coding: utf-8 -*-
"""GAS 폰트 렌더 — GBU 확정 모델(448px 4bpp 선형텍스처, 플레인 인터리브) 그대로 적용.
off=(r*14+y)*224 + c*7 + x//2 ; nsh=(x홀?4:0)+(plane?2:0) ; val=(byte>>nsh)&3"""
import numpy as np, os
from PIL import Image
OUT = r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas"
fnt = open(os.path.join(OUT,"font_j14x14.bin"),"rb").read()
ROWB, CW, CH, COLS = 224, 14, 14, 32
PAL=np.array([255,170,85,0],dtype=np.uint8)
nglyph=6976

def render(ti):
    cell, plane = ti//2, ti%2
    r, c = divmod(cell, COLS)
    m=np.zeros((CH,CW),np.uint8)
    for y in range(CH):
        for x in range(CW):
            off=(r*CH+y)*ROWB + c*7 + x//2
            nsh=(4 if x%2 else 0) + (2 if plane else 0)
            m[y,x]=(fnt[off]>>nsh)&3
    return m

def atlas(start, cols=32, rows=24, scale=3):
    cp=CW+2
    img=np.full((rows*cp*scale, cols*cp*scale),40,dtype=np.uint8)
    for gi in range(rows*cols):
        ti=start+gi
        if ti>=nglyph: break
        gray=PAL[render(ti)]
        big=np.kron(gray,np.ones((scale,scale),dtype=np.uint8))
        rr=gi//cols; cc=gi%cols
        img[rr*cp*scale:rr*cp*scale+CH*scale, cc*cp*scale:cc*cp*scale+CW*scale]=big
    return Image.fromarray(img,'L')

atlas(0).save(os.path.join(OUT,"C_atlas_0.png"))
atlas(768).save(os.path.join(OUT,"C_atlas_768.png"))
atlas(2000).save(os.path.join(OUT,"C_atlas_2000.png"))
print("C_atlas_0/768/2000.png 저장 (GBU 확정 모델)")
