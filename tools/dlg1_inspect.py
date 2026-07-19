# -*- coding: utf-8 -*-
"""2d_dialog_1.gim 정밀 분석: 팔레트, 라벨 픽셀 위치(불투명 인덱스)."""
import sys, io, os, struct
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")
import gaslib as G, gimutil as GU
from PIL import Image
import numpy as np

s,e=None,None
for ss in G.fsets():
    if ss["nfiles"]==0: continue
    try: ents=G.fset_entries(ss)
    except: continue
    for ee in ents:
        if ee["name"].endswith("data/menu/dialog/2d_dialog_1.gim"): s,e=ss,ee
    if s: break
d=G.fset_read(s,e)
blocks=GU.gim_blocks(d)
img=pal=None
for b in blocks:
    info=GU.gim_sub_info(d,b)
    if info["bpp"] in (4,8) and info["w"]>1 and info["h"]>1: img=(b,info)
    else:
        try: pal=GU.gim_palette(d,info)
        except: pass
b,info=img
print("팔레트(idx: RGBA):")
for i,c in enumerate(pal): print(f"  {i}: {c}")
raw=d[info["pix_start"]:info["pix_start"]+info["pix_len"]]
lin=GU.unswizzle(raw,info["rowbytes"],info["halign"]) if info["order"]==1 else raw
grid=np.array(GU.read_indices(lin,info))
print("인덱스 히스토그램:", {int(k):int(v) for k,v in zip(*np.unique(grid,return_counts=True))})
# 불투명(알파>0) 인덱스 집합
opaque=[i for i,c in enumerate(pal) if c[3]>40]
print("불투명 인덱스:",opaque)
mask=np.isin(grid,opaque)
# 열별/행별 불투명 분포로 라벨 위치 파악
ys,xs=np.where(mask)
print(f"불투명 픽셀 bbox: x[{xs.min()}~{xs.max()}] y[{ys.min()}~{ys.max()}]")
# 텍스트를 흑백으로 크게 저장(불투명=검정)
vis=np.where(mask,0,255).astype(np.uint8)
Image.fromarray(vis,'L').resize((info["w"]*5,info["h"]*5),Image.NEAREST).save(os.path.join(G.BASE,"dlg1_text.png"))
print("dlg1_text.png 저장 (불투명=검정)")
