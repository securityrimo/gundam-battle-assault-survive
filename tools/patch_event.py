# -*- coding: utf-8 -*-
"""event.csv(gundam.dat flat, fileset 사본 없음) 한글화.
글로벌 kr_map(build_kr 산출)로 인코딩. flat이므로 크기 ≤ 원본이면 idx 크기필드 갱신 in-place."""
import sys, io, os, struct, json, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G
import build_kr as B   # sanitize (patch_menu 경유 stdout utf-8 래핑)

POC=os.path.join(os.path.dirname(G.ISO),"Gundam Assault Survive (Korean_PoC).iso")
kr=json.load(io.open(os.path.join(G.BASE,"kr_map_global.json"),encoding="utf-8"))  # {글자:[ti,code]}

def enc(s):
    out=bytearray()
    for ch in s:
        if "가"<=ch<="힣": out+=struct.pack(">H",kr[ch][1])
        else: out+=ch.encode("cp932")
    return bytes(out)

# 원본 event.csv (flat) — 행 구조 기준
orig=G.gfile("/data/menu/mission/event/event.csv")
text=orig.decode("cp932"); sep="\r\n" if "\r\n" in text else "\n"
orows=[ln.split(",") for ln in text.split(sep)]
# Codex 최종본(csv_ko_utf8) 데이터행 사용, 필드명행(0,1)은 원본 유지
kp=os.path.join(G.BASE,"csv_ko_utf8","data","menu","mission","event","event.csv")
korows=list(csv.reader(io.open(kp,encoding="utf-8-sig",newline="")))
rows=[]
for ri in range(len(orows)):
    if ri<2 or ri>=len(korows): rows.append(orows[ri])
    else: rows.append([B.sanitize(c) for c in korows[ri]])
new=enc(sep.join(",".join(r) for r in rows))

# idx 엔트리 #268: off/size
IDX_ENT=268
idx=G.rd(G.IDX_LBA,0,G.IDX_SIZE)
hdr=struct.unpack_from("<I",idx,0xc)[0]
t,no,a,off,size,dd=struct.unpack_from("<6I",idx,hdr+IDX_ENT*24)
print(f"event.csv 원본 usize={size}, 한글 usize={len(new)}, fit={len(new)<=size}")
if len(new)>size:
    print("초과 — gundam.dat 재패킹 필요(현재 미구현). 중단."); raise SystemExit(1)

# PoC ISO 기록: gundam.dat 데이터 + idx size 필드
f=open(POC,"r+b")
f.seek(G.GDAT_LBA*G.SECTOR+off); f.write(new)
# 남은 공간은 원본 잔여바이트가 남지만 size 갱신으로 미읽음
size_field=G.IDX_LBA*G.SECTOR + hdr + IDX_ENT*24 + 16
f.seek(size_field); f.write(struct.pack("<I",len(new)))
f.close()
print(f"event.csv 기록 완료(gundam.dat off={off}), idx size {size}->{len(new)}")

# 오프라인 검증
f=open(POC,"rb"); f.seek(G.GDAT_LBA*G.SECTOR+off); rb=f.read(len(new)); f.close()
rev={code:ch for ch,(ti,code) in kr.items()}
txt=rb.decode("cp932")
out=[]
for ch in txt:
    try: code=struct.unpack(">H",ch.encode("cp932"))[0] if len(ch.encode("cp932"))==2 else None
    except: code=None
    out.append(rev.get(code,ch))
recon="".join(out); nk=sum(1 for c in recon if "가"<=c<="힣")
print("검증 한글자수",nk)
for ln in recon.split(sep)[:4]: print("  ",ln[:70])
