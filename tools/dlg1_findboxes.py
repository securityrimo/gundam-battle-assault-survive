# -*- coding: utf-8 -*-
"""원본 일본어 라벨 4개(はい/戻る/いいえ/OK)의 정확한 tight bbox 산출."""
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

def cluster_cols(cols_present, gap=3):
    """연속 열 구간 클러스터"""
    runs=[]; start=None; last=None
    for x in cols_present:
        if start is None: start=x; last=x
        elif x-last<=gap: last=x
        else: runs.append((start,last)); start=x; last=x
    if start is not None: runs.append((start,last))
    return runs

def row_labels(y0,y1):
    band=mask[y0:y1,:]
    colpres=[x for x in range(band.shape[1]) if band[:,x].any() and x>=44]  # 우측만
    runs=cluster_cols(colpres, gap=3)
    res=[]
    for (cx0,cx1) in runs:
        sub=mask[y0:y1, cx0:cx1+1]
        ys,xs=np.where(sub)
        by0=y0+ys.min(); by1=y0+ys.max()+1
        res.append((cx0,by0,cx1+1,by1))
    return res

print("상단행(y1~18) 라벨 bbox:", row_labels(1,18))
print("하단행(y20~37) 라벨 bbox:", row_labels(20,37))
