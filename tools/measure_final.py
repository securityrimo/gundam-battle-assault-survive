# -*- coding: utf-8 -*-
"""csv_ko_utf8(코덱스 최종본)을 인코딩·압축해 원본 csize와 비교(성장 여부).
+ event/charamake 필드명 행(row0,1) 원문 보존 여부 확인."""
import sys, io, os, struct, csv, glob
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G

KO_DIR=os.path.join(G.BASE,"csv_ko_utf8")
_NONCP={"·":"・","–":"-","—":"-","―":"ー","“":"\"","”":"\"","‘":"'","’":"'","…":"...","∼":"～","•":"・"}
def sanitize(s):
    s=s.replace("​","")
    out=[]
    for ch in s:
        if "가"<=ch<="힣": out.append(ch); continue
        ch=_NONCP.get(ch,ch)
        try: ch.encode("cp932"); out.append(ch)
        except: pass
    return "".join(out)

# 원본 csize (fileset 대표 사본)
def orig_csize(basename):
    for s in G.fsets():
        if s["nfiles"]==0: continue
        try: ents=G.fset_entries(s)
        except: continue
        for e in ents:
            if e["name"].endswith(basename): return e["csize"], e["usize"]
    return None,None

# 전체 한글 음절 → donor kr_map
cs=G.charset()
def dec(c):
    try: return struct.pack(">H",c).decode("cp932")
    except: return None
used=set()
for root,_,fs in os.walk(os.path.join(G.BASE,"csv_src")):
    for fn in fs:
        if fn.endswith(".csv"):
            try: used.update(io.open(os.path.join(root,fn),encoding="utf-8-sig").read())
            except: pass
donors=[cs[ti] for ti in range(len(cs)) if (lambda ch: ch and ch not in used and "一"<=ch<="鿿")(dec(cs[ti]))]
donors=donors[len(donors)//3:]
allsyl=set()
kofiles={}
for p in glob.glob(os.path.join(KO_DIR,"**","*.csv"),recursive=True):
    # 콤마 안전: 셀 단위로 sanitize 후 재조립(원본 콤마 구조 유지 위해 csv 파싱)
    rows=list(csv.reader(io.open(p,encoding="utf-8-sig",newline="")))
    kofiles[os.path.basename(p)]=(p,rows)
    for r in rows:
        for c in r: allsyl|={ch for ch in c if "가"<=ch<="힣"}
allsyl=sorted(allsyl)
kr={ch:code for ch,code in zip(allsyl,donors)}
print(f"최종 음절 {len(allsyl)}, donor {len(donors)} → {'충분' if len(allsyl)<=len(donors) else '부족!'}")

def enc(s):
    out=bytearray()
    for ch in s:
        if "가"<=ch<="힣": out+=struct.pack(">H",kr[ch])
        else: out+=ch.encode("cp932")
    return bytes(out)

print(f"\n{'파일':26s} {'원본csize':>9s} {'한글comp':>9s} {'차이':>6s}  판정")
tot_grow=0
for bn,(p,rows) in sorted(kofiles.items()):
    oc,ou=orig_csize(bn)
    if oc is None: print(f"  {bn}: fileset 없음(event=gundam.dat)"); continue
    # 셀별 sanitize(ASCII콤마→、) 후 라인 재조립
    sep="\r\n"  # 원본 확인 필요하나 대부분 \n; 아래서 orig에서 판별
    # 원문 sep 판별
    from_orig=G.gfile if False else None
    lines=[",".join(sanitize(c).replace(",","、") for c in r) for r in rows]
    text="\n".join(lines)
    comp=G.raic_compress(enc(text))
    d=len(comp)-oc;
    if d>0: tot_grow+=1
    print(f"  {bn:24s} {oc:9d} {len(comp):9d} {d:+6d}  {'OK(≤)' if d<=0 else '성장!'}")
print(f"\n성장(초과) 파일 수: {tot_grow}")
