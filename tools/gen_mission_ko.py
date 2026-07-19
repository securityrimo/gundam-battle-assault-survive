# -*- coding: utf-8 -*-
"""fileset 미션 CSV 243개 → ex_bonus/qualification/lose 셀만 한글 치환해
csv_ko_utf8/data/mission/*.csv 생성(그 외 행은 원본 그대로)."""
import io, sys, os
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
BASE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,BASE)
import gaslib as G
from compose_mission import compose

outdir=os.path.join(BASE,'csv_ko_utf8','data','mission')
os.makedirs(outdir,exist_ok=True)
n=0; cells=0; seen=set()
for s in G.fsets():
    for e in G.fset_entries(s):
        if '/mission/' not in e['name'] or not e['name'].endswith('.csv'): continue
        base=e['name'].split('/')[-1]
        if base in seen: continue
        seen.add(base)
        d=G.fset_read(s,e).decode('cp932')
        sep='\r\n' if '\r\n' in d else '\n'
        out=[]; sec=None
        for ln in d.split(sep):
            f=ln.split(',')
            if f[0]=='CsvCategory': sec=f[1]; out.append(ln); continue
            if sec in ('ex_bonus','qualification','lose') and f[0] and f[0]!='str':
                ko,ok=compose(f[0])
                if ok and ko.strip():
                    f[0]=ko; cells+=1
                out.append(','.join(f))
            else:
                out.append(ln)
        io.open(os.path.join(outdir,base),'w',encoding='utf-8',newline='').write(sep.join(out))
        n+=1
print(f'{n}파일 생성, {cells}셀 번역')
