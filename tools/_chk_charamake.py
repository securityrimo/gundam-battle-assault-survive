# -*- coding: utf-8 -*-
import csv, io
rows=list(csv.reader(io.open('translate/charamake_data.csv',encoding='utf-8-sig',newline='')))
out=io.open('_chk.txt','w',encoding='utf-8')
bad=0
for r in rows[1:]:
    ko=r[4] if len(r)>4 else ''
    for ch in ko:
        if '가'<=ch<='힣': continue
        if ch in '\\n': continue
        try: ch.encode('cp932')
        except:
            bad+=1; out.write('cp932X %r in %s\n'%(ch, ko[:24])); break
out.write('=== 샘플 6 ===\n')
for r in rows[1:7]:
    out.write('JP: '+r[3][:56]+'\n')
    out.write('KO: '+((r[4] if len(r)>4 else ''))[:56]+'\n\n')
out.write('cp932 불가 셀 수: %d / %d\n'%(bad, len(rows)-1))
out.close(); print('done')
