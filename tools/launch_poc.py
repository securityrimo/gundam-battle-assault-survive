# -*- coding: utf-8 -*-
"""PoC ISO 실행 + 부팅 후 스크린샷."""
import sys, os, time
sys.path.insert(0, r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu")
import ppsspp as P

POC = r"C:\Emul\Switch\패치유틸.xdeltaUI\Gundam Assault Survive (Korean_PoC).iso"
OUT = r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas"

print("launching PPSSPP with PoC ISO...")
P.launch(iso=POC, wait=25)
hwnd = P.find_window()
print("hwnd:", hwnd)
if not hwnd:
    print("PPSSPP 창을 못 찾음"); sys.exit(1)
P.focus(hwnd)
P.shot(hwnd, os.path.join(OUT, "poc_shot_00_boot.png"))
print("saved poc_shot_00_boot.png")
