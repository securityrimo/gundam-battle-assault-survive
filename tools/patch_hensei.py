# -*- coding: utf-8 -*-
"""편성 화면 GIM(불투명/반투명 배경 + 밝은 글자) 라벨 한글화.
지우기=박스 최빈 인덱스, 글자=배경↔흰색 블렌드 최근접 팔레트색."""
import sys, io, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")
import gaslib as G, gimutil as GU
from patch_cham_gim import render
from collections import Counter
from PIL import Image

FG=(255,255,255,255)

LABELS_NAME=[  # 2d_hensei_name.gim 128x128
 ("출격",0,0,30,14,"center"),("대기",31,0,61,14,"center"),("저장",62,0,92,14,"center"),
 ("불러오기",0,15,56,29,"center"),("사용 안 함",57,15,127,29,"center"),
 ("SFS선택",0,30,71,44,"center"),("편성완료",72,30,124,44,"center"),
 ("출격횟수",0,45,49,58,"center"),("소대 스톡",50,45,110,58,"center"),
 ("출격",0,59,29,77,"center"),("대기",30,59,60,77,"center"),
 ("대기",70,83,126,108,"center"),
]
LABELS_03=[("편성완료",0,0,74,24,"center")]  # 2d_hensei_03.gim 96x24

def patch(data,labels):
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
    def bright(i):
        r,g,b2,a=pal[i]; return (r+g+b2)/3>=120 and a>=140
    def nearest(rgba):
        best=0;bd=1e18
        for i,c in enumerate(pal):
            d=sum((c[k]-rgba[k])**2 for k in range(4))
            if d<bd: bd=d;best=i
        return best
    for lab in labels:
        text,x0,y0,x1,y1=lab[:5]; align=lab[5] if len(lab)>5 else "left"
        x1=min(x1,info["w"]); y1=min(y1,info["h"])
        c=Counter(grid[y][x] for y in range(y0,y1) for x in range(x0,x1) if not bright(grid[y][x]))
        bg=c.most_common(1)[0][0] if c else 0
        bgc=pal[bg]
        cache={}
        def cov2idx(a):
            if a not in cache:
                t=a/255.0
                cache[a]=nearest(tuple(round(bgc[k]+(FG[k]-bgc[k])*t) for k in range(4)))
            return cache[a]
        for y in range(y0,y1):
            for x in range(x0,x1): grid[y][x]=bg
        if not text: continue
        cov=render(text,x1-x0,y1-y0,align)
        for yy in range(y1-y0):
            for xx in range(x1-x0):
                a=int(cov[yy,xx])
                if a>=25: grid[y0+yy][x0+xx]=cov2idx(a)
    newlin=GU.write_indices(grid,info)
    packed=GU.swizzle(newlin,info["rowbytes"],info["halign"]) if info["order"]==1 else bytes(newlin)
    out=bytearray(data); out[info["pix_start"]:info["pix_start"]+info["pix_len"]]=packed
    return bytes(out),info,pal,grid

if __name__=="__main__":
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
    s=next(x for x in G.fsets() if x["name"]=="menu_mission")
    for nm,labs in [("2d_hensei_name.gim",LABELS_NAME),("2d_hensei_03.gim",LABELS_03)]:
        e=next(x for x in G.fset_entries(s) if x["name"].endswith(nm))
        data=G.fset_read(s,e)
        nd,info,pal,grid=patch(data,labs)
        comp=G.raic_compress(nd)
        print(f"{nm}: {e['csize']} -> {len(comp)} {'OK' if len(comp)<=e['csize'] else 'OVER'}")
        im=Image.new("RGBA",(info["w"],info["h"])); px=im.load()
        for y in range(info["h"]):
            for x in range(info["w"]): px[x,y]=tuple(pal[grid[y][x]])
        bg=Image.new("RGBA",im.size,(60,60,80,255)); bg.alpha_composite(im)
        bg.convert("RGB").resize((info["w"]*2,info["h"]*2),Image.NEAREST).save(os.path.join(G.BASE,nm.replace(".gim","_after.png")))
    print("previews saved")
