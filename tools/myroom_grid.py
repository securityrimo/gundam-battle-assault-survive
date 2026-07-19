# -*- coding: utf-8 -*-
"""2d_myroom_01.gim 을 좌표격자와 함께 크게 렌더 + 팔레트 출력(라벨 박스 좌표 확정용)."""
import sys, io, os
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")
import gaslib as G, gimutil as GU
import numpy as np
from PIL import Image, ImageDraw

s=next(x for x in G.fsets() if x["name"]=="main_menu")
e=next(x for x in G.fset_entries(s) if x["name"].endswith("2d_myroom_01.gim"))
data=G.fset_read(s,e)
blocks=GU.gim_blocks(data); img=pal=None
for b in blocks:
    info=GU.gim_sub_info(data,b)
    if info["bpp"] in (4,8) and info["w"]>4 and info["h"]>4 and img is None: img=(b,info)
    else:
        try: pal=GU.gim_palette(data,info)
        except: pass
b,info=img
raw=data[info["pix_start"]:info["pix_start"]+info["pix_len"]]
lin=GU.unswizzle(raw,info["rowbytes"],info["halign"]) if info["order"]==1 else raw
grid=np.array(GU.read_indices(lin,info))
W,H=info["w"],info["h"]
print("size",W,H,"bpp",info["bpp"],"pal",len(pal))
print("palette:", [(i,c) for i,c in enumerate(pal)])
im=Image.new("RGBA",(W,H)); px=im.load()
for y in range(H):
    for x in range(W): px[x,y]=tuple(pal[grid[y][x]])
sc=5
big=Image.new("RGBA",(W*sc,H*sc),(20,20,40,255)); big.alpha_composite(im.resize((W*sc,H*sc),Image.NEAREST))
d=ImageDraw.Draw(big)
for gx in range(0,W+1,10):
    d.line([(gx*sc,0),(gx*sc,H*sc)],fill=(255,80,80,120))
    d.text((gx*sc+1,1),str(gx),fill=(255,255,0,255))
for gy in range(0,H+1,10):
    d.line([(0,gy*sc),(W*sc,gy*sc)],fill=(255,80,80,120))
    d.text((1,gy*sc+1),str(gy),fill=(255,255,0,255))
big.convert("RGB").save(os.path.join(G.BASE,"myroom01_grid.png"))
print("myroom01_grid.png 저장")
