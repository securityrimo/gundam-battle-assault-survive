# -*- coding: utf-8 -*-
import io,sys,json
sys.path.insert(0,'.')
import compose_mission as CM  # stdout 래핑은 여기서 1회
import gaslib as G
from collections import Counter
uniq=Counter(); nfiles=0
for s in G.fsets():
    for e in G.fset_entries(s):
        if '/locate/' not in e['name'] or not e['name'].endswith('.csv'): continue
        nfiles+=1
        d=G.fset_read(s,e).decode('cp932')
        for ln in d.replace('\r\n','\n').split('\n'):
            f=ln.split(',')
            if len(f)>2 and f[0] not in ('CsvCategory','NAME') and f[2].strip():
                t=f[2].strip()
                if any('぀'<=c<='ヿ' or '一'<=c<='鿿' for c in t): uniq[t]+=1
print('locate files',nfiles,'uniq',len(uniq))
ok=0; bad=[]
for t in uniq:
    ko,fine=CM.compose(t)
    if fine: ok+=1
    else: bad.append(t)
print('compose ok',ok,'fail',len(bad))
json.dump(dict(uniq),open('_locate_names.json','w',encoding='utf-8'),ensure_ascii=False)
io.open('_locate_left.txt','w',encoding='utf-8').write('\n'.join(sorted(bad)))
