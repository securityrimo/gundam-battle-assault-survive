# -*- coding: utf-8 -*-
"""(1) GAS charset(ELF 0x3aad24) vs GBU charset(BOOT.BIN 0x2e71e0) 동일성 비교.
(2) 글리프↔코드 대응 검증: charset[ti] 디코드 문자와 폰트 글리프 시각 대조용 렌더."""
import struct, os
import numpy as np
from PIL import Image

GAS=r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas"
GBU=r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gbu"
elf=open(os.path.join(GAS,"EBOOT_dec.elf"),"rb").read()
GAS_ST, LN = 0x3aad24, 6953
gas_codes=struct.unpack_from(f">{LN}H", elf, GAS_ST)

boot=open(os.path.join(GBU,"BOOT.BIN"),"rb").read()
GBU_ST=0x2e71e0
gbu_codes=struct.unpack_from(f">{LN}H", boot, GBU_ST)

same=sum(1 for a,b in zip(gas_codes,gbu_codes) if a==b)
print(f"charset 비교: {same}/{LN} 일치 ({100*same/LN:.2f}%)")
if same!=LN:
    diff=[(i,hex(gas_codes[i]),hex(gbu_codes[i])) for i in range(LN) if gas_codes[i]!=gbu_codes[i]]
    print("불일치 예시(최대 10):", diff[:10])

# 글리프↔코드 대응 검증용: 특정 인덱스의 코드 디코드 + 글리프 렌더
fnt=open(os.path.join(GAS,"font_j14x14.bin"),"rb").read()
ROWB,CW,CH,COLS=224,14,14,32
PAL=np.array([255,170,85,0],dtype=np.uint8)
def render(ti):
    cell,plane=ti//2,ti%2; r,c=divmod(cell,COLS)
    m=np.zeros((CH,CW),np.uint8)
    for y in range(CH):
        for x in range(CW):
            off=(r*CH+y)*ROWB+c*7+x//2
            nsh=(4 if x%2 else 0)+(2 if plane else 0)
            m[y,x]=(fnt[off]>>nsh)&3
    return m
def dec(c):
    try: return struct.pack(">H",c).decode("cp932")
    except: return "?"

# 몇 개 인덱스 대응 출력 + 대조 이미지(코드가 가리키는 문자 = 글리프여야 함)
picks=[1,2,10,50,100,200,300,846,2469]  # 2469=GBU에서 '가' 자리였음
lines=[]
scale=6; cp=CW+2
img=np.full((cp*scale, len(picks)*cp*scale),40,np.uint8)
for k,ti in enumerate(picks):
    ch=dec(gas_codes[ti])
    lines.append(f"  ti={ti}: code={hex(gas_codes[ti])} -> '{ch}'")
    gray=PAL[render(ti)]; big=np.kron(gray,np.ones((scale,scale),np.uint8))
    img[0:CH*scale, k*cp*scale:k*cp*scale+CW*scale]=big
Image.fromarray(img,'L').save(os.path.join(GAS,"charset_verify.png"))
print("인덱스별 코드→문자 (charset_verify.png의 글리프와 대조):")
open(os.path.join(GAS,"_charset_picks.txt"),"w",encoding="utf-8").write("\n".join(lines))
print("\n".join(lines))
