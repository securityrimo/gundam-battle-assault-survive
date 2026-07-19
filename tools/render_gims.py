# -*- coding: utf-8 -*-
"""후보 UI GIM들을 렌더해 텍스트 내용 확인(재도색 계획용)."""
import sys, io, os
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")
import gaslib as G, gimutil as GU
import numpy as np
from PIL import Image

def get(name):
    for s in G.fsets():
        if s["nfiles"]==0: continue
        try: ents=G.fset_entries(s)
        except: continue
        for e in ents:
            if e["name"].endswith(name): return G.fset_read(s,e)
    return None

def render(data,outpng):
    try: blocks=GU.gim_blocks(data)
    except Exception as ex: print("  블록실패",ex); return
    img=pal=None
    for b in blocks:
        info=GU.gim_sub_info(data,b)
        if info["bpp"] in (4,8) and info["w"]>1 and info["h"]>1 and img is None: img=(b,info)
        else:
            try: pal=GU.gim_palette(data,info)
            except: pass
    if not img: print("  이미지블록 없음"); return
    b,info=img
    raw=data[info["pix_start"]:info["pix_start"]+info["pix_len"]]
    lin=GU.unswizzle(raw,info["rowbytes"],info["halign"]) if info["order"]==1 else raw
    grid=GU.read_indices(lin,info)
    im=Image.new("RGBA",(info["w"],info["h"])); px=im.load()
    for y in range(info["h"]):
        for x in range(info["w"]): px[x,y]=tuple(pal[grid[y][x]]) if pal and grid[y][x]<len(pal) else (grid[y][x],)*3+(255,)
    bg=Image.new("RGBA",im.size,(30,30,50,255)); bg.alpha_composite(im)
    sc=3 if max(info["w"],info["h"])<300 else 1
    bg.convert("RGB").resize((info["w"]*sc,info["h"]*sc),Image.NEAREST).save(outpng)
    print(f"  {info['w']}x{info['h']} bpp{info['bpp']} -> {outpng}")

for name in ["tune/sel_paramoji.gim","pause_menu/p_menu_iia0.gim","pause_menu/p_menu_iia1.gim",
             "platoon/2d_hensei_name.gim","custom_pilot/cham_menu_moji.gim","fesark/2d_fude_situ.gim"]:
    d=get(name)
    print(name, "found" if d else "MISSING")
    if d: render(d, os.path.join(G.BASE,"gim_"+name.split("/")[-1].replace(".gim","")+".png"))
