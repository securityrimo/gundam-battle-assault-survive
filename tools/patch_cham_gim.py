# -*- coding: utf-8 -*-
"""파일럿 생성/관리 GIM 라벨 한글화.
cham_menu_moji.gim: 名前/性別/容姿/声/出身地/適性検査 → 이름/성별/외모/음성/출신지/적성검사
cham_para_1.gim: 体力/反応/射撃/敏捷/格闘/技量/命中/感知/防御 → 체력/반응/사격/민첩/격투/기량/명중/감지/방어 (SP 유지)
회색(64,64,64) 알파램프 팔레트. 자리교체(픽셀만), 크기 불변."""
import sys, io, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")
import gaslib as G, gimutil as GU
import numpy as np
from PIL import Image, ImageFont, ImageDraw

KRFONT=r"C:\Windows\Fonts\malgunbd.ttf"
TARGETS={
 # 声(음성)은 크롭폭 1글자라 한글 2자가 잘림 → 원본 유지(크롭테이블 미규명)
 "cham_menu_moji.gim":[("이름",2,2,28,14),("성별",2,16,28,28),("외모",2,30,28,42),
                       ("출신지",2,57,40,70),("적성검사",2,72,52,84)],
 "cham_para_1.gim":[("체력",2,2,29,14),("반응",29,2,56,14),("사격",2,16,29,28),("민첩",29,16,56,28),
                    ("격투",2,30,29,42),("기량",29,30,56,42),("명중",2,44,29,56),("감지",29,44,56,56),
                    ("방어",2,58,29,70)],
 # 옵션 메뉴 버튼 라벨(흰색 알파램프, 우측정렬). BGM/HOW TO/on/off 유지.
 "opt_02.gim":[("컨트롤",0,3,79,15,"right"),("세이브/로드",0,18,79,31,"right"),
               ("볼륨",0,35,79,47,"right"),("시크릿",0,51,79,63,"right"),
               ("커스텀 사운드",0,67,79,79,"right"),("데이터 설치",0,83,79,95,"right")],
 # 포즈 메뉴 아틀라스(흰색 알파램프). 영문 MENU/LOG/VIEWPOINT/SOUND LIST/CONDITION·〔〕 유지.
 "p_menu_iia1.gim":[("승리",1,2,28,16),("패배",29,2,58,16),("조건",60,2,88,16),
                    ("전투 복귀",1,17,58,31),("콕핏",76,17,126,30),
                    ("시점 변경",1,31,50,44),("후방",63,31,89,44),("시점",91,31,118,44),
                    ("BGM 변경",1,45,60,58),("",71,58,127,65),("전투 로그",71,45,127,58),
                    ("전체 맵·",1,58,62,72),
                    ("작전 중단",1,73,50,85),("로그 확인",79,73,126,85,"right")],
}

def gray_ramp(pal):
    # 모노크롬(회색/흰색) 알파램프 자동 감지: r==g==b 계열 중 최대 그룹
    from collections import defaultdict
    fam=defaultdict(list)
    for i,c in enumerate(pal):
        cr,cg,cb,ca=c
        if abs(cr-cg)<6 and abs(cg-cb)<6: fam[cr//32].append((i,ca))
    best=max(fam.values(),key=len) if fam else [(0,0)]
    r=list(best); r.append((0,0))
    return sorted(set(r),key=lambda x:x[1])

def a2i(ramp,a):
    best=ramp[0][0]; bd=999
    for i,av in ramp:
        if abs(av-a)<bd: bd=abs(av-a); best=i
    return best

def render(text,w,h,align="left"):
    # 1px 여백(상하좌우) — 원본 라벨의 숨쉴 틈 유지
    for size in range(h-2,6,-1):
        f=ImageFont.truetype(KRFONT,size); bb=f.getbbox(text)
        if bb[2]-bb[0]<=w-2 and bb[3]-bb[1]<=h-2: break
    img=Image.new("L",(w,h),0); dr=ImageDraw.Draw(img)
    bb=f.getbbox(text); tw=bb[2]-bb[0]; th=bb[3]-bb[1]
    x0 = (w-tw-1) if align=="right" else ((w-tw)//2 if align=="center" else 1)
    dr.text((x0-bb[0],(h-th)//2-bb[1]),text,fill=255,font=f)
    return np.asarray(img)

def patch(data,labels):
    img=pal=None
    for b in GU.gim_blocks(data):
        info=GU.gim_sub_info(data,b)
        if info["bpp"] in (4,8) and info["w"]>4 and info["h"]>4 and img is None: img=info
        else:
            try: pal=GU.gim_palette(data,info)
            except: pass
    info=img; ramp=gray_ramp(pal)
    raw=data[info["pix_start"]:info["pix_start"]+info["pix_len"]]
    lin=GU.unswizzle(raw,info["rowbytes"],info["halign"]) if info["order"]==1 else raw
    grid=[r[:] for r in GU.read_indices(lin,info)]
    for lab in labels:
        text,x0,y0,x1,y1=lab[:5]; align=lab[5] if len(lab)>5 else "left"
        x1=min(x1,info["w"]); y1=min(y1,info["h"])
        for y in range(y0,y1):
            for x in range(x0,x1): grid[y][x]=0  # 투명으로 지움
        if not text: continue  # 지우기 전용
        cov=render(text,x1-x0,y1-y0,align)
        for yy in range(y1-y0):
            for xx in range(x1-x0):
                a=int(cov[yy,xx])
                if a>=25: grid[y0+yy][x0+xx]=a2i(ramp,a)
    newlin=GU.write_indices(grid,info)
    packed=GU.swizzle(newlin,info["rowbytes"],info["halign"]) if info["order"]==1 else bytes(newlin)
    out=bytearray(data); out[info["pix_start"]:info["pix_start"]+info["pix_len"]]=packed
    return bytes(out),info,pal,grid

if __name__=="__main__":
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
    s=next(x for x in G.fsets() if x["name"]=="scene_custom_chara")
    for nm,labels in TARGETS.items():
        e=next(x for x in G.fset_entries(s) if x["name"].endswith(nm))
        data=G.fset_read(s,e)
        nd,info,pal,grid=patch(data,labels)
        comp=G.raic_compress(nd)
        print(f"{nm}: comp {e['csize']} -> {len(comp)} {'OK' if len(comp)<=e['csize'] else '초과'}")
        im=Image.new("RGBA",(info["w"],info["h"])); px=im.load()
        for y in range(info["h"]):
            for x in range(info["w"]): px[x,y]=tuple(pal[grid[y][x]])
        bg=Image.new("RGBA",im.size,(200,200,210,255)); bg.alpha_composite(im)
        o=nm.replace(".gim","_after.png")
        bg.convert("RGB").resize((info["w"]*3,info["h"]*3),Image.NEAREST).save(os.path.join(G.BASE,o))
        print("  →",o)
