# -*- coding: utf-8 -*-
"""2d_dialog_*.gim 을 fileset에서 추출·렌더해 버튼 내용 확인."""
import sys, io, os, struct
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")
import gaslib as G
import gimutil as GU
from PIL import Image

def find(basename):
    for s in G.fsets():
        if s["nfiles"]==0: continue
        try: ents=G.fset_entries(s)
        except: continue
        for e in ents:
            if e["name"].endswith(basename):
                return s,e
    return None,None

def render(data, outpng):
    blocks=GU.gim_blocks(data)
    img=None; pal=None
    for b in blocks:
        info=GU.gim_sub_info(data,b)
        if info["bpp"] in (4,8) and info["w"]>1 and info["h"]>1 and img is None:
            img=(b,info)
        else:
            # palette 후보
            try:
                p=GU.gim_palette(data,info)
                pal=p
            except Exception: pass
    if not img: print("  이미지 블록 못찾음"); return
    b,info=img
    raw=data[info["pix_start"]:info["pix_start"]+info["pix_len"]]
    lin=GU.unswizzle(raw, info["rowbytes"], info["halign"]) if info["order"]==1 else raw
    grid=GU.read_indices(lin, info)
    im=Image.new("RGBA",(info["w"],info["h"]))
    px=im.load()
    for y in range(info["h"]):
        for x in range(info["w"]):
            idx=grid[y][x]
            px[x,y]=tuple(pal[idx]) if pal and idx<len(pal) else (idx,idx,idx,255)
    im.resize((info["w"]*3,info["h"]*3),Image.NEAREST).save(outpng)
    print(f"  {info['w']}x{info['h']} bpp{info['bpp']} fmt{info['fmt']} order{info['order']} pal={len(pal) if pal else 0} -> {outpng}")

for bn in ["data/menu/dialog/2d_dialog_0.gim","data/menu/dialog/2d_dialog_1.gim","data/ark/shop/2d_dialog_1.gim"]:
    s,e=find(bn)
    if not s: print(bn,"없음"); continue
    d=G.fset_read(s,e)
    print(f"{bn} [{s['name']}] usize={len(d)} magic={d[:4]}")
    render(d, os.path.join(G.BASE,"dlg_"+bn.split('/')[-1].replace('.gim','')+("_"+s['name'])+".png"))
