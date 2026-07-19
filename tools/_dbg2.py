# -*- coding: utf-8 -*-
import fes_worksheet as FW, io, csv
t='{B=W}{C=356E4D}エリアＡ{CE}{BE}、{B=W}{C=334572}ＨＬＶ{CE}{BE}が離陸準備中です'
ko,ok=FW.tl_line(t)
def kb(s):
    n=0
    for c in s:
        if c=='\n': n+=1
        elif '가'<=c<='힣': n+=2
        else:
            try: n+=len(c.encode('cp932'))
            except: n+=2
    return n
rows=list(csv.DictReader(io.open('translate/fes_tl.csv',encoding='utf-8-sig',newline='')))
r=[x for x in rows if x['원문']==t]
slot=r[0]['slot'] if r else '?'
tr=r[0]['번역'] if r else '?'
au=(r[0]['자동번역'][:44] if r else '?')
out='ok=%s kbstrip=%d slot=%s\nko=%r\nrow_tr=%r\nrow_auto=%r'%(ok,kb(ko.replace(' ','')),slot,ko,tr,au)
io.open('_dbg.txt','w',encoding='utf-8').write(out)
