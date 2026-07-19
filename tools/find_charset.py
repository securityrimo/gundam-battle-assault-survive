# -*- coding: utf-8 -*-
"""EBOOT_dec.elf 에서 charset 테이블(글리프인덱스→SJIS, 빅엔디안 u16) 탐색.
GBU: BOOT.BIN 0x2e71e0, 6953개. GAS: ELF 어딘가, ~6976개 예상.
판정: 유효 cp932 2바이트 코드가 긴 런으로 이어지는 구간."""
import struct, os
OUT=r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas"
elf=open(os.path.join(OUT,"EBOOT_dec.elf"),"rb").read()
print("elf size",len(elf))

def valid_sjis_be(hi, lo):
    # cp932 2바이트: lead 0x81-0x9F,0xE0-0xFC ; trail 0x40-0x7E,0x80-0xFC
    if not ((0x81<=hi<=0x9F) or (0xE0<=hi<=0xFC)): return False
    if not ((0x40<=lo<=0x7E) or (0x80<=lo<=0xFC)): return False
    return True

# 슬라이딩: 각 오프셋에서 연속 유효 SJIS u16 개수
best=[]
i=0; N=len(elf)
runs=[]
while i+2<=N:
    hi,lo=elf[i],elf[i+1]
    if valid_sjis_be(hi,lo):
        j=i; cnt=0
        while j+2<=N and valid_sjis_be(elf[j],elf[j+1]):
            cnt+=1; j+=2
        if cnt>=500:
            runs.append((i,cnt))
        i=j
    else:
        i+=2
# 홀수 정렬도 시도
i=1
while i+2<=N:
    hi,lo=elf[i],elf[i+1]
    if valid_sjis_be(hi,lo):
        j=i; cnt=0
        while j+2<=N and valid_sjis_be(elf[j],elf[j+1]):
            cnt+=1; j+=2
        if cnt>=500:
            runs.append((i,cnt))
        i=j
    else:
        i+=2

runs.sort(key=lambda x:-x[1])
print("긴 SJIS-BE 런(오프셋, 개수) 상위:")
for off,cnt in runs[:15]:
    codes=struct.unpack_from(f">{min(cnt,8)}H",elf,off)
    print(f"  off=0x{off:06x} cnt={cnt}  first8={[hex(c) for c in codes]}")
