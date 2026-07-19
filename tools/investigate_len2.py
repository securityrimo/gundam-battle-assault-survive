# -*- coding: utf-8 -*-
"""히트 오프셋들을 번들/영역으로 분류. csize·usize·off 참조의 정체 규명."""
import sys, io, os, struct
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaslib as G

TOTAL=187423360
fdat=G.rd(G.FSET_LBA,0,TOTAL)
head=fdat[:0x50]
s1_off,s1_size,s2_off,s2_size=struct.unpack_from("<4I",head,0x18)
sets=[s for s in G.fsets()]
sd=sorted([s for s in sets if s["size"]>0],key=lambda x:x["off"])

def region(off):
    if off<0x50: return "header"
    if s1_off<=off<s1_off+s1_size: return f"sec1(dir) +{off-s1_off}"
    if s2_off<=off<s2_off+s2_size: return "sec2(names)"
    # 어느 번들?
    for s in sd:
        if s["off"]<=off<s["off"]+s["size"]:
            rel=off-s["off"]
            try:
                bb=fdat[s["off"]:s["off"]+min(s["size"],0x14)]
                m,nf,tbl,ntbl,dstart=struct.unpack_from("<4s4I",bb,0)
                if m==b"FSTS":
                    if tbl<=rel<ntbl:
                        idx=(rel-tbl)//16; field=(rel-tbl)%16
                        fn={0:"nameoff",4:"off",8:"usize",12:"csize"}.get(field,f"+{field}")
                        return f"{s['name']} FSTS테이블 엔트리#{idx}.{fn}"
                    elif ntbl<=rel<dstart: return f"{s['name']} 이름섹션"
                    else: return f"{s['name']} 데이터 +{rel}"
            except: pass
            return f"{s['name']} +{rel}"
    return "?"

hits={
 "csize(13610)":[0x69982c,0x78f13c],
 "usize(31332)":[0x141c,0x699828,0x6999b4,0x78f138,0x797cd4],
 "off(36048)":[0x78f134,0x2a2d8f4,0x2a3a094,0x2a53134,0x2a5f804,0x2a785e4,0x2a857c4,0x3044844,0x8b138f4],
}
for label,offs in hits.items():
    print(f"\n{label}:")
    for o in offs:
        print(f"  0x{o:x}: {region(o)}")
