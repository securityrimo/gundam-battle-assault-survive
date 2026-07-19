# -*- coding: utf-8 -*-
"""sel_paramoji.gim(126x132) 스탯 라벨 아틀라스 한글화. 4개 번들 공용 사본.
모든 한글이 원 라벨과 같거나 짧아 tight bbox 내 재도색(정렬 유지) — 크롭 안전."""
import sys, io, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")
import gaslib as G
from patch_cham_gim import patch
from PIL import Image

# (text,x0,y0,x1,y1,align) — 지우기=셀 경계 전체, 렌더 정렬로 원 라벨 위치 유지(크롭 안전). HP/SP// 유지.
LABELS=[
 ("잔여포인트",0,0,56,12,"left"),      ("돌진공격력",56,0,126,12,"right"),
 ("실탄방어",0,12,64,24,"right"),      ("명중률",64,12,126,24,"right"),
 ("빔방어",0,24,64,36,"right"),        ("연사횟수",64,24,126,36,"right"),
 # 우측 열은 좌측 라벨 크롭(+~6px)에 안 걸리게 시작을 오른쪽으로 민다(지우기는 경계 전체)
 ("기동성",0,36,44,48,"right"),        ("칭호",46,36,70,48,"right"),  ("위력",100,36,126,48,"right"),
 ("스러스터출력",0,48,64,60,"right"),  ("탄속",64,48,96,60,"right"),  ("탄수",96,48,126,60,"right"),
 ("스러스터속도",0,60,64,72,"right"),  ("체력",64,60,96,72,"right"),  ("사격",96,60,126,72,"right"),
 ("레이더성능",0,72,64,84,"right"),    ("격투",64,72,96,84,"right"),  ("명중",96,72,126,84,"right"),
 ("밸런서",0,84,64,96,"right"),        ("방어",64,84,96,96,"right"),  ("반응",96,84,126,96,"right"),
 ("선회속도",0,96,64,108,"right"),     ("민첩",64,96,96,108,"right"), ("기량",96,96,126,108,"right"),
 ("리로드성능",0,108,69,120,"right"),  ("감지",72,108,98,120,"right"),
 ("소지금",0,120,38,132,"left"),       ("내구력",39,120,74,132,"right"),
]

if __name__=="__main__":
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
    s=next(x for x in G.fsets() if x["name"]=="menu_mission")
    e=next(x for x in G.fset_entries(s) if x["name"].endswith("sel_paramoji.gim"))
    data=G.fset_read(s,e)
    nd,info,pal,grid=patch(data,LABELS)
    comp=G.raic_compress(nd)
    print(f"sel_paramoji: comp {e['csize']} -> {len(comp)} {'OK' if len(comp)<=e['csize'] else '초과'}")
    im=Image.new("RGBA",(info["w"],info["h"])); px=im.load()
    for y in range(info["h"]):
        for x in range(info["w"]): px[x,y]=tuple(pal[grid[y][x]])
    bg=Image.new("RGBA",im.size,(215,215,225,255)); bg.alpha_composite(im)
    bg.convert("RGB").resize((info["w"]*4,info["h"]*4),Image.NEAREST).save(os.path.join(G.BASE,"sel_paramoji_after.png"))
    print("→ sel_paramoji_after.png")
