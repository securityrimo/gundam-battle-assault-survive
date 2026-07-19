# -*- coding: utf-8 -*-
"""우측 일본어 라벨 4개의 정확한 bbox 산출."""
import sys, io, os
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")
import gaslib as G, gimutil as GU
import numpy as np

for ss in G.fsets():
    if ss["nfiles"]==0: continue
    try: ents=G.fset_entries(ss)
    except: continue
    e=next((x for x in ents if x["name"].endswith("data/menu/dialog/2d_dialog_1.gim")),None)
    if e: s=ss; break
d=G.fset_read(s,e)
blocks=GU.gim_blocks(d); img=pal=None
for b in blocks:
    info=GU.gim_sub_info(d,b)
    if info["bpp"] in (4,8) and info["w"]>1 and info["h"]>1: img=(b,info)
    else:
        try: pal=GU.gim_palette(d,info)
        except: pass
b,info=img
raw=d[info["pix_start"]:info["pix_start"]+info["pix_len"]]
lin=GU.unswizzle(raw,info["rowbytes"],info["halign"]) if info["order"]==1 else raw
grid=np.array(GU.read_indices(lin,info))
opaque=[i for i,c in enumerate(pal) if c[3]>40]
mask=np.isin(grid,opaque)
# 우측(x>=46)만
def bbox(sub, x0,x1,y0,y1):
    m=mask[y0:y1,x0:x1]
    ys,xs=np.where(m)
    if len(xs)==0: return None
    return (x0+xs.min(),y0+ys.min(),x0+xs.max()+1,y0+ys.max()+1, int(m.sum()))
# 행 분리: 상단/하단 (y 히스토그램)
rowsum=mask[:, 46:].sum(1)
print("행별 불투명(46~):", [int(v) for v in rowsum])
# 열 분리(우측): 라벨 사이 빈 열 찾기
colsum=mask[:, 46:].sum(0)
print("열별(46~):", [int(v) for v in colsum])
