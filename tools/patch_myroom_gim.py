# -*- coding: utf-8 -*-
"""2d_myroom_01.gim 대시보드 일본어 라벨 → 한글 재도색. 흰색 알파램프(idx9~15).
각 박스: 배경(박스 최빈 인덱스)으로 지우고 한글 흰색 렌더. 영문/MS/기호는 그대로."""
import sys, io, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")
import gaslib as G, gimutil as GU
import numpy as np
from PIL import Image, ImageFont, ImageDraw

KRFONT=r"C:\Windows\Fonts\malgunbd.ttf"
# myroom_00.ark TXOS 11~17, 49~50에서 확인한 실제 크롭 셀.
# 이 경계 밖을 지우면 이웃 스프라이트가 훼손되고, 셀보다 크게 그리면 게임의
# 고정 crop에서 잘리므로 좌표를 임의로 넓히지 않는다.
LABELS=[("출격 횟수",1,46,50,60),("격추수",1,61,38,75),("파츠",41,61,77,75),
        ("피격추수",1,76,50,90),("파일럿",1,91,61,105),("미션",1,106,61,120),
        ("소지금",193,87,230,101),("플레이 시간",193,102,253,116)]
WHITE=[(9,0),(10,41),(11,73),(12,119),(13,159),(14,199),(15,253)]
def a2i(a):
    best=9;bd=999
    for i,av in WHITE:
        if abs(av-a)<bd: bd=abs(av-a);best=i
    return best

def load():
    s=next(x for x in G.fsets() if x["name"]=="main_menu")
    e=next(x for x in G.fset_entries(s) if x["name"].endswith("2d_myroom_01.gim"))
    return G.fset_read(s,e)

def render_ko(text,w,h):
    for size in range(h,7,-1):
        f=ImageFont.truetype(KRFONT,size); bb=f.getbbox(text)
        if bb[2]-bb[0]<=w-1 and bb[3]-bb[1]<=h: break
    img=Image.new("L",(w,h),0); dr=ImageDraw.Draw(img)
    bb=f.getbbox(text); th=bb[3]-bb[1]
    dr.text((1-bb[0],(h-th)//2-bb[1]),text,fill=255,font=f)  # 좌측정렬
    return np.asarray(img)

def patch(data):
    # 2d_myroom_01의 투명 팔레트는 0번이 아니다. 샵에서 검증한 안전 패처는
    # 실제 최소 알파 인덱스를 찾아 지우므로 검은 사각형 잔재가 생기지 않는다.
    from patch_shop import patch_alpha
    return patch_alpha(data,LABELS)

if __name__=="__main__":
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
    d=load(); nd,info,pal,grid=patch(d)
    im=Image.new("RGBA",(info["w"],info["h"])); px=im.load()
    for y in range(info["h"]):
        for x in range(info["w"]): px[x,y]=tuple(pal[grid[y][x]])
    bg=Image.new("RGBA",im.size,(20,24,45,255)); bg.alpha_composite(im)
    bg.convert("RGB").resize((info["w"]*4,info["h"]*4),Image.NEAREST).save(os.path.join(G.BASE,"myroom01_after.png"))
    print("myroom01_after.png 저장")
