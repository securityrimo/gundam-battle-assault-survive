# -*- coding: utf-8 -*-
"""2d_dialog_1.gim 의 일본어 버튼 라벨(はい/戻る/いいえ)을 한글로 재도색.
알파-램프 팔레트(흰색 alpha 0..255=idx 9..15)에 맞춰 한글 렌더. OK는 유지.
반환: 수정된 GIM 바이트. 미리보기 PNG 저장."""
import sys, io, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")
import gaslib as G, gimutil as GU
import numpy as np
from PIL import Image, ImageFont, ImageDraw

KRFONT=r"C:\Windows\Fonts\malgunbd.ttf"
# 엔진 크롭과 일치하는 원본 라벨 정확 bbox (dlg1_findboxes.py 측정).
# 한글을 이 박스 그대로 그려야 인게임에서 안 잘림.
LABELS=[("예",   51,2,81,18),   # はい
        ("뒤로", 94,2,125,18),  # 戻る
        ("아니오",51,21,96,37), # いいえ
        ("OK",  100,21,126,36)] # OK
# 지우기: 각 라벨 박스 ±1px (원본 글자 완전 삭제)
CLEAR=[(x0-1,y0-1,x1+1,y1+1) for _,x0,y0,x1,y1 in LABELS]

WHITE_RAMP=[(9,0),(10,25),(11,55),(12,97),(13,145),(14,193),(15,255)]  # (idx, alpha)
def alpha_to_idx(a):
    best=9;bd=999
    for idx,av in WHITE_RAMP:
        if abs(av-a)<bd: bd=abs(av-a);best=idx
    return best

def get_gim(name):
    for ss in G.fsets():
        if ss["nfiles"]==0: continue
        try: ents=G.fset_entries(ss)
        except: continue
        for ee in ents:
            if ee["name"].endswith(name): return ss,ee
    return None,None

def render_label(text, w, h):
    """박스(w,h)에 맞춰 한글 렌더 → coverage(0..255) 배열"""
    # 폰트 크기 자동: 높이의 ~0.9, 폭 초과 방지
    for size in range(h, 7, -1):
        f=ImageFont.truetype(KRFONT,size)
        bb=f.getbbox(text); tw=bb[2]-bb[0]; th=bb[3]-bb[1]
        if tw<=w-1 and th<=h: break
    img=Image.new("L",(w,h),0); dr=ImageDraw.Draw(img)
    bb=f.getbbox(text); tw=bb[2]-bb[0]; th=bb[3]-bb[1]
    x=(w-tw)//2-bb[0]; y=(h-th)//2-bb[1]
    dr.text((x,y),text,fill=255,font=f)
    return np.asarray(img)

def patch(data):
    blocks=GU.gim_blocks(data); img=pal=None
    for b in blocks:
        info=GU.gim_sub_info(data,b)
        if info["bpp"] in (4,8) and info["w"]>1 and info["h"]>1: img=(b,info)
        else:
            try: pal=GU.gim_palette(data,info)
            except: pass
    b,info=img
    raw=data[info["pix_start"]:info["pix_start"]+info["pix_len"]]
    lin=GU.unswizzle(raw,info["rowbytes"],info["halign"]) if info["order"]==1 else raw
    grid=[row[:] for row in GU.read_indices(lin,info)]
    # 지우기(원본 일본어 완전 삭제)
    for cx0,cy0,cx1,cy1 in CLEAR:
        for y in range(cy0,cy1):
            for x in range(cx0,cx1):
                grid[y][x]=9
    for text,x0,y0,x1,y1 in LABELS:
        cov=render_label(text, x1-x0, y1-y0)
        for yy in range(y1-y0):
            for xx in range(x1-x0):
                a=int(cov[yy,xx])
                if a>=13: grid[y0+yy][x0+xx]=alpha_to_idx(a)
    # 재인코딩
    newlin=GU.write_indices(grid, info)
    packed=GU.swizzle(newlin, info["rowbytes"], info["halign"]) if info["order"]==1 else bytes(newlin)
    out=bytearray(data); out[info["pix_start"]:info["pix_start"]+info["pix_len"]]=packed
    return bytes(out), info, pal, grid

if __name__=="__main__":
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
    s,e=get_gim("data/menu/dialog/2d_dialog_1.gim")
    d=G.fset_read(s,e)
    nd,info,pal,grid=patch(d)
    # 미리보기(팔레트 적용)
    im=Image.new("RGBA",(info["w"],info["h"])); px=im.load()
    for y in range(info["h"]):
        for x in range(info["w"]):
            px[x,y]=tuple(pal[grid[y][x]])
    # 검은 배경 합성해서 흰 글자 보이게
    bg=Image.new("RGBA",im.size,(20,20,40,255)); bg.alpha_composite(im)
    bg.convert("RGB").resize((info["w"]*5,info["h"]*5),Image.NEAREST).save(os.path.join(G.BASE,"dlg1_after.png"))
    print("dlg1_after.png 저장 (한글 재도색 미리보기)")
