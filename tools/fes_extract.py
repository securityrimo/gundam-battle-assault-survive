# -*- coding: utf-8 -*-
"""GAS FES 문자열 전수 추출(fileset의 data/script/*.fes) → fes_strings.json
GBU 41_fes_extract와 동일 구조 가정: hdr+8 u16[12], v[9]=풀 시작, NUL종단 SJIS."""
import struct, os, sys, json, io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
BASE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,BASE)
import gaslib as G

def fes_pool(d):
    v=struct.unpack_from("<12H", d, 8)
    return v[9]
def has_jp(s):
    return any("぀"<=c<="ヿ" or "一"<=c<="鿿" or c in "。、！？・ー" for c in s)

entries=[]; files=0; badpool=0
seen=set()
for s in G.fsets():
    for e in G.fset_entries(s):
        n=e['name']
        if not n.endswith('.fes') or n in seen: continue
        seen.add(n)
        d=G.fset_read(s,e)
        if len(d)<32: continue
        files+=1
        pool=fes_pool(d)
        if not (0<pool<len(d)): badpool+=1; continue
        pos=pool
        while pos<len(d):
            end=d.find(b"\x00",pos)
            if end<0: end=len(d)
            raw=d[pos:end]
            if raw:
                try: txt=raw.decode("shift-jis")
                except UnicodeDecodeError: txt=None
                if txt and has_jp(txt):
                    entries.append({"file":n,"bundle":s['name'],"off":pos,"len":len(raw),"text":txt})
            pos=end+1
json.dump(entries,open(os.path.join(BASE,"fes_strings.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=0)
uniq={}
for e in entries: uniq[e["text"]]=uniq.get(e["text"],0)+1
print(f"fes 파일 {files} (pool이상 {badpool}), JP문자열 {len(entries)}, 고유 {len(uniq)}, 총 {sum(e['len'] for e in entries)}B")
w=io.open(os.path.join(BASE,"fes_sample.txt"),"w",encoding="utf-8")
for e in entries[:60]: w.write(f"{e['file']} +{e['off']:#x} ({e['len']}B)\n{e['text']}\n---\n")
w.close()
