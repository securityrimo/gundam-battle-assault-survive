# -*- coding: utf-8 -*-
import io,json,csv
import fes_worksheet as FW
ui=json.load(open('eboot_ui.json',encoding='utf-8'))
sh=json.load(open('eboot_ui_short.json',encoding='utf-8'))
tr=set()
for r in csv.DictReader(io.open('translate/eboot_ui.csv',encoding='utf-8-sig',newline='')):
    if r.get('번역','').strip(): tr.add(int(r['key'].split('|')[1]))
def kb(s):
    n=0
    for c in s:
        if c=='\n': n+=1
        elif '가'<=c<='힣': n+=2
        else:
            try: n+=len(c.encode('cp932'))
            except: n+=2
    return n
rows=[]
for e in ui:
    off=e['offs'][0][0]
    if off in tr or e['text'] in sh: continue
    if not (3400000<=off<=3800000): continue
    if not all('぀'<=c<='ヿ' or '一'<=c<='鿿' or c in '、。・ー（）()「」　 ' or c.isascii() for c in e['text']): continue
    ko,ok=FW.tl_line(e['text'])
    if ok and ko.strip() and kb(ko.replace(' ',''))>e['slot']:
        rows.append((e['slot'],kb(ko.replace(' ','')),e['text'],ko))
rows.sort()
io.open('_title_over.txt','w',encoding='utf-8').write('\n'.join('%d|%d|%s|%s'%(a,b,c,d) for a,b,c,d in rows))
io.open('_title_cnt.txt','w',encoding='utf-8').write(str(len(rows)))
