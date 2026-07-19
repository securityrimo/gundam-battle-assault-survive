# -*- coding: utf-8 -*-
"""cp_sel_1.gim(328x72, 8bpp) 파일럿 관리목록 스탯 라벨 한글화.
불투명/반투명 배경 스트립 → 배경(idx238)으로 지우고, 글자=배경↔(64,64,64,255) 블렌드의 최근접 팔레트색."""
import sys, io, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")
import gaslib as G, gimutil as GU
from patch_cham_gim import render
from PIL import Image

# (text,x0,y0,x1,y1) — 원 라벨(2한자) 실측 x±2. SP 유지.
LABELS=[("체력",3,3,28,17),("사격",35,3,61,17),("격투",69,3,94,17),("명중",101,3,126,17),
        ("방어",135,3,161,17),("반응",167,3,192,17),("민첩",199,3,225,17),("기량",233,3,258,17),
        ("감지",265,3,291,17)]
BG=238; FG=(64,64,64,255)

def patch(data,labels=LABELS):
    img=pal=None
    for b in GU.gim_blocks(data):
        info=GU.gim_sub_info(data,b)
        if info["bpp"] in (4,8) and info["w"]>4 and info["h"]>4 and img is None: img=info
        else:
            try: pal=GU.gim_palette(data,info)
            except: pass
    info=img
    raw=data[info["pix_start"]:info["pix_start"]+info["pix_len"]]
    lin=GU.unswizzle(raw,info["rowbytes"],info["halign"]) if info["order"]==1 else raw
    grid=[r[:] for r in GU.read_indices(lin,info)]
    bgc=pal[BG]
    def nearest(rgba):
        best=0;bd=1e18
        for i,c in enumerate(pal):
            d=sum((c[k]-rgba[k])**2 for k in range(4))
            if d<bd: bd=d;best=i
        return best
    cache={}
    def cov2idx(a):
        if a in cache: return cache[a]
        t=a/255.0
        rgba=tuple(round(bgc[k]+(FG[k]-bgc[k])*t) for k in range(4))
        cache[a]=nearest(rgba); return cache[a]
    for text,x0,y0,x1,y1 in labels:
        for y in range(y0,y1):
            for x in range(x0,x1): grid[y][x]=BG
        cov=render(text,x1-x0,y1-y0,"center")
        for yy in range(y1-y0):
            for xx in range(x1-x0):
                a=int(cov[yy,xx])
                if a>=20: grid[y0+yy][x0+xx]=cov2idx(a)
    newlin=GU.write_indices(grid,info)
    packed=GU.swizzle(newlin,info["rowbytes"],info["halign"]) if info["order"]==1 else bytes(newlin)
    out=bytearray(data); out[info["pix_start"]:info["pix_start"]+info["pix_len"]]=packed
    return bytes(out),info,pal,grid

if __name__=="__main__":
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
    s=next(x for x in G.fsets() if x["name"]=="scene_custom_chara")
    e=next(x for x in G.fset_entries(s) if x["name"].endswith("cp_sel_1.gim"))
    data=G.fset_read(s,e)
    nd,info,pal,grid=patch(data)
    comp=G.raic_compress(nd)
    print(f"cp_sel_1: comp {e['csize']} -> {len(comp)} {'OK' if len(comp)<=e['csize'] else '초과'}")
    im=Image.new("RGBA",(info["w"],info["h"])); px=im.load()
    for y in range(info["h"]):
        for x in range(info["w"]): px[x,y]=tuple(pal[grid[y][x]])
    bg=Image.new("RGBA",im.size,(215,215,225,255)); bg.alpha_composite(im)
    bg.convert("RGB").resize((info["w"]*3,info["h"]*3),Image.NEAREST).save(os.path.join(G.BASE,"cp_sel_1_after.png"))
    print("→ cp_sel_1_after.png")
