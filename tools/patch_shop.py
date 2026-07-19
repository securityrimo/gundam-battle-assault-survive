# -*- coding: utf-8 -*-
"""샵 GIM 라벨 한글화. moji_0/1=윤곽선 텍스트(외곽선+본체), moji_2/3=흰색 알파램프."""
import sys, io, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")
import gaslib as G, gimutil as GU
from patch_cham_gim import render, gray_ramp, a2i
import numpy as np
from PIL import Image

# moji_0 (128x128): 흰 글자+검은 외곽선. 영문(SHOP/MS/MA/SFS/U.C./SUBFLIGHT/NEW/시대숫자/SEED/00/EXTRA/OTHER/Lv:/SPA:/×/=) 유지
L0=[("소지금",1,1,34,12,"center"),("비고",55,1,75,11),("제한",77,1,97,11),
    ("사이즈",64,12,90,22),("랭크",64,23,90,33),("/상황",64,34,92,44),
    ("필요G",63,45,92,55),
    ("특성",64,56,90,66),
    ("소지수",64,67,96,77),
    ("종류",64,78,86,88),
    ("명칭",1,96,21,106),("개발계획명",64,100,115,110),
    ("칭호",1,107,21,117),
    # shop.ark TXOS 75~80의 실제 크롭 영역. 앞의 기존 추정 영역이 경계를
    # 침범할 수 있으므로 버튼 라벨은 반드시 마지막에 지우고 다시 그린다.
    ("파일럿",1,40,62,53,"right"),
    ("칭호",1,54,26,67,"right"),("파츠",28,54,62,67,"right"),
    ("개발",1,68,26,81,"right"),("스킬",28,68,62,81,"right"),
    ("시크릿",1,82,62,95,"right")]
# moji_1 (128x64): 탭(あーさ/たーは/まーわ/英語/記号) + 計画/スキル名. 영문 유지
L1=[("아-사",1,1,34,15),("타-하",1,16,34,26),("마-와",1,26,34,41),
    ("영어",0,42,27,62),("기호",28,42,53,62),
    # shop.ark TXOS 127의 실제 계획 스프라이트는 (56,50) 25x13이다.
    # 개발(TXOS 79)과 같은 크기·정렬로 렌더해야 조합 시 기준선이 맞는다.
    ("계획",56,50,81,63,"right"),
    ("스킬명",81,42,127,62)]
# moji_2 (128x32) 흰알파: 基礎ＭＳ/カスタムパーツ/必要チューンポイント (ー 유지)
L2=[("기초 MS",0,0,46,13),("커스텀 파츠",49,0,124,13),("필요 튜닝 포인트",0,14,106,27)]
# moji_3 (128x32) 흰알파: MS/MA/SFS名(名만), パーツ名, 名前, シークレット (INFORMATION 유지)
L3=[("명",61,0,68,12),("파츠명",89,1,127,11),("이름",0,12,21,24),("시크릿",55,12,108,24)]

def load(nm):
    s=next(x for x in G.fsets() if x["name"]=="scene_shop")
    e=next(x for x in G.fset_entries(s) if x["name"].endswith(nm))
    return G.fset_read(s,e), e["csize"]

def patch_alpha(data, labels):
    """샵 팔레트용 알파램프 패처.

    공용 patch_cham_gim.patch는 팔레트 0번을 투명색으로 가정하지만,
    shop_moji_0/1은 0번이 반투명 검정이고 실제 투명색은 각각 12/9번이다.
    0번으로 셀을 지우면 인게임에서 검은 잔상·획이 남으므로 알파가 가장
    낮은 팔레트 엔트리를 직접 찾아 사용한다.
    """
    img=pal=None
    for b in GU.gim_blocks(data):
        info=GU.gim_sub_info(data,b)
        if info["bpp"] in (4,8) and info["w"]>4 and info["h"]>4 and img is None:
            img=info
        else:
            try: pal=GU.gim_palette(data,info)
            except: pass
    info=img
    clear=min(range(len(pal)), key=lambda i: pal[i][3])
    ramp=gray_ramp(pal)
    raw=data[info["pix_start"]:info["pix_start"]+info["pix_len"]]
    lin=GU.unswizzle(raw,info["rowbytes"],info["halign"]) if info["order"]==1 else raw
    grid=[r[:] for r in GU.read_indices(lin,info)]
    for lab in labels:
        text,x0,y0,x1,y1=lab[:5]
        align=lab[5] if len(lab)>5 else "left"
        x1=min(x1,info["w"]); y1=min(y1,info["h"])
        for y in range(y0,y1):
            for x in range(x0,x1):
                grid[y][x]=clear
        if not text:
            continue
        cov=render(text,x1-x0,y1-y0,align)
        for yy in range(y1-y0):
            for xx in range(x1-x0):
                alpha=int(cov[yy,xx])
                if alpha>=25:
                    grid[y0+yy][x0+xx]=a2i(ramp,alpha)
    newlin=GU.write_indices(grid,info)
    packed=GU.swizzle(newlin,info["rowbytes"],info["halign"]) if info["order"]==1 else bytes(newlin)
    out=bytearray(data)
    out[info["pix_start"]:info["pix_start"]+info["pix_len"]]=packed
    return bytes(out),info,pal,grid

def patch_outline(data, labels):
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
    def nearest(rgba):
        best=0;bd=1e18
        for i,c in enumerate(pal):
            d=sum((c[k]-rgba[k])**2 for k in range(4))
            if d<bd: bd=d;best=i
        return best
    WHITE=nearest((230,230,230,255)); MID=nearest((150,150,150,255)); DARK=nearest((40,40,40,210))
    for lab in labels:
        text,x0,y0,x1,y1=lab[:5]
        x1=min(x1,info["w"]); y1=min(y1,info["h"])
        for y in range(y0,y1):
            for x in range(x0,x1): grid[y][x]=0
        if not text: continue
        cov=render(text,x1-x0,y1-y0,"left")
        h,w=cov.shape
        core=cov>=110
        # 드롭섀도(+1,+1)만 — 원본 스타일
        for yy in range(h):
            for xx in range(w):
                if core[yy,xx]:
                    sy,sx=y0+yy+1,x0+xx+1
                    if sy<y1 and sx<x1 and not (yy+1<h and xx+1<w and core[yy+1,xx+1]):
                        grid[sy][sx]=DARK
        for yy in range(h):
            for xx in range(w):
                if core[yy,xx]: grid[y0+yy][x0+xx]=WHITE
                elif cov[yy,xx]>=50: grid[y0+yy][x0+xx]=MID
    newlin=GU.write_indices(grid,info)
    packed=GU.swizzle(newlin,info["rowbytes"],info["halign"]) if info["order"]==1 else bytes(newlin)
    out=bytearray(data); out[info["pix_start"]:info["pix_start"]+info["pix_len"]]=packed
    return bytes(out),info,pal,grid

# 원본 글리프 실측: 흰색 알파램프(idx15 본체 + AA) — 다이얼로그와 동일 방식이 정답
TARGETS={"shop_moji_0.gim":(patch_alpha,L0),"shop_moji_1.gim":(patch_alpha,L1),
         "shop_moji_2.gim":(patch_alpha,L2),"shop_moji_3.gim":(patch_alpha,L3)}

if __name__=="__main__":
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
    for nm,(fn,labs) in TARGETS.items():
        data,csize=load(nm)
        nd,info,pal,grid=fn(data,labs)
        comp=G.raic_compress(nd)
        print(f"{nm}: {csize} -> {len(comp)} {'OK' if len(comp)<=csize else 'OVER'}")
        im=Image.new("RGBA",(info["w"],info["h"])); px=im.load()
        for y in range(info["h"]):
            for x in range(info["w"]): px[x,y]=tuple(pal[grid[y][x]])
        bg=Image.new("RGBA",im.size,(200,205,215,255)); bg.alpha_composite(im)
        bg.convert("RGB").resize((info["w"]*3,info["h"]*3),Image.NEAREST).save(os.path.join(G.BASE,nm.replace(".gim","_after.png")))
    print("previews saved")
