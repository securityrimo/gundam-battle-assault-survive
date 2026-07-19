# -*- coding: utf-8 -*-
"""locate 표시명 번역 함수(글로서리>수동명단>조합기). build_kr에서 in-place 사용."""
import os, csv, io
BASE=os.path.dirname(os.path.abspath(__file__))
from compose_mission import compose
from locate_names_ko import NAMES

_GL=None
def _gl():
    global _GL
    if _GL is None:
        _GL={}
        for r in csv.DictReader(open(os.path.join(BASE,'CHARACTER_GLOSSARY.csv'),encoding='utf-8-sig')):
            _GL[r['original_jp'].strip()]=r['standard_ko'].strip()
    return _GL

def has_jp(s): return any('぀'<=c<='ヿ' or '一'<=c<='鿿' for c in s)

def tl(t):
    t=t.strip()
    g=_gl()
    if t in g: return g[t]
    if t in NAMES: return NAMES[t]
    ko,ok=compose(t)
    return ko if ok and ko.strip() else None

def tl_locate_text(txt):
    """locate CSV 전체 텍스트에서 col2(表示名)만 번역. (새텍스트, 치환수)"""
    sep='\r\n' if '\r\n' in txt else '\n'
    out=[]; n=0
    for ln in txt.split(sep):
        f=ln.split(',')
        if len(f)>2 and f[0] not in ('CsvCategory','NAME') and f[2].strip() and has_jp(f[2]):
            ko=tl(f[2])
            if ko: f[2]=ko; n+=1
        out.append(','.join(f))
    return sep.join(out), n

def need_syllables():
    """전체 고유 표시명 번역의 한글 음절 집합(need용)."""
    import json
    s=set()
    p=os.path.join(BASE,'_locate_names.json')
    if os.path.exists(p):
        for t in json.load(open(p,encoding='utf-8')):
            ko=tl(t)
            if ko:
                for c in ko:
                    if '가'<=c<='힣': s.add(c)
    return s
