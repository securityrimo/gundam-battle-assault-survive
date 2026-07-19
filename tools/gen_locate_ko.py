# -*- coding: utf-8 -*-
"""locate CSV 658개 → 表示名(col2)만 한글 치환해 csv_ko_utf8/data/locate/ 생성.
우선순위: CHARACTER_GLOSSARY > locate_names_ko.NAMES > compose_mission."""
import io, sys, os, csv
BASE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,BASE)
from compose_mission import compose   # stdout 래핑 1회
import gaslib as G
from locate_names_ko import NAMES

GL={}
for r in csv.DictReader(open(os.path.join(BASE,'CHARACTER_GLOSSARY.csv'),encoding='utf-8-sig')):
    GL[r['original_jp'].strip()]=r['standard_ko'].strip()

def tl(t):
    if t in GL: return GL[t]
    if t in NAMES: return NAMES[t]
    ko,ok=compose(t)
    return ko if ok and ko.strip() else None

outdir=os.path.join(BASE,'csv_ko_utf8','data','locate')
os.makedirs(outdir,exist_ok=True)
n=cells=miss=0; seen=set(); missset=set()
for s in G.fsets():
    for e in G.fset_entries(s):
        if '/locate/' not in e['name'] or not e['name'].endswith('.csv'): continue
        base=e['name'].split('/')[-1]
        if base in seen: continue
        seen.add(base)
        d=G.fset_read(s,e).decode('cp932')
        sep='\r\n' if '\r\n' in d else '\n'
        out=[]
        for ln in d.split(sep):
            f=ln.split(',')
            if len(f)>2 and f[0] not in ('CsvCategory','NAME') and f[2].strip() and any('぀'<=c<='ヿ' or '一'<=c<='鿿' for c in f[2]):
                ko=tl(f[2].strip())
                if ko: f[2]=ko; cells+=1
                else: miss+=1; missset.add(f[2].strip())
            out.append(','.join(f))
        io.open(os.path.join(outdir,base),'w',encoding='utf-8',newline='').write(sep.join(out))
        n+=1
print(f'{n} files, {cells} cells translated, {miss} missed ({len(missset)} uniq)')
for t in sorted(missset)[:20]: print('  miss:',t)
