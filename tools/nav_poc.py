# -*- coding: utf-8 -*-
"""이미 실행 중인 PPSSPP에서 타이틀→메인메뉴로 진행하며 스크린샷."""
import sys, os, time
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")
import ppsspp as P
OUT = r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas"
hwnd = P.find_window()
if not hwnd:
    print("PPSSPP 창 없음"); sys.exit(1)
P.focus(hwnd)
seq = sys.argv[1] if len(sys.argv)>1 else "enter,enter,x,enter,x"
tag = sys.argv[2] if len(sys.argv)>2 else "nav"
for i,k in enumerate(seq.split(",")):
    k=k.strip()
    if k.startswith("wait"):
        time.sleep(float(k[4:] or 2)); continue
    P.key(P.VK[k]); time.sleep(1.5)
time.sleep(2)
path=os.path.join(OUT, f"poc_shot_{tag}.png")
P.shot(hwnd, path)
print("saved", path)
