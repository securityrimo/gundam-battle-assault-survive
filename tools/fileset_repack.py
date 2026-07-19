# -*- coding: utf-8 -*-
"""fileset.dat(PIDX0) 재패커 — 번들간/파일간 패딩 회수하며 재직렬화.
디렉토리(sec1/sec2)·번들명·파일명·순서 불변. sec1 doff/dsize, FSTS off/usize/csize만 갱신.
번들 정렬 0x800, 파일 정렬 0x10. 총 크기 ≤ 원본이면 in-place 덮어쓰기 가능.
new_files: {(bundle_name, file_name): (stored_bytes, usize)} — stored_bytes=슬롯에 넣을 최종 바이트(RAIC압축본 등).
"""
import struct

FSET_LBA=325328; SECTOR=2048; TOTAL=187423360
BUNDLE_ALIGN=0x800; FILE_ALIGN=0x10

def _align(x,a): return (x+a-1)&~(a-1)
def _file_align(off):
    """원본 오프셋이 놓인 최대 2의 거듭제곱 정렬(≤0x800). 밀릴 때 이 정렬을 보존."""
    for a in (0x800,0x400,0x200,0x100,0x80,0x40,0x20,0x10):
        if off % a == 0: return a
    return 1

class Fileset:
    def __init__(self, iso_path):
        self.iso_path=iso_path
        f=open(iso_path,"rb"); f.seek(FSET_LBA*SECTOR); self.data=bytearray(f.read(TOTAL)); f.close()
        d=self.data
        self.header=bytes(d[:0x50])
        self.s1_off,self.s1_size,self.s2_off,self.s2_size=struct.unpack_from("<4I",d,0x18)
        self.sec1=bytearray(d[self.s1_off:self.s1_off+self.s1_size])
        self.sec2=bytes(d[self.s2_off:self.s2_off+self.s2_size])
        self.cnt=struct.unpack_from("<I",self.sec1,0)[0]
        self.rec_offs=list(struct.unpack_from(f"<{self.cnt}I",self.sec1,4))
        self.bundles=[]
        for i in range(self.cnt):
            ro=self.rec_offs[i]
            nameoff,flags,doff,dsize,nf=struct.unpack_from("<5I",self.sec1,ro)
            e=self.sec2.index(b"\x00",nameoff); name=self.sec2[nameoff:e].decode("ascii")
            self.bundles.append({"i":i,"rec":ro,"name":name,"flags":flags,"doff":doff,"dsize":dsize,"nf":nf})
        self.first_doff=min(b["doff"] for b in self.bundles if b["dsize"]>0)

    def _bundle_raw(self,b): return self.data[b["doff"]:b["doff"]+b["dsize"]]

    def parse_bundle_files(self,b):
        if b["nf"]==0: return None
        bb=self._bundle_raw(b)
        magic,nf,tbl,ntbl,dstart=struct.unpack_from("<4s4I",bb,0)
        assert magic==b"FSTS",(b["name"],magic)
        files=[]
        for i in range(nf):
            nameoff,off,usize,csize=struct.unpack_from("<4I",bb,tbl+16*i)
            e=bb.index(b"\x00",ntbl+nameoff); nm=bb[ntbl+nameoff:e].decode("ascii")
            files.append({"idx":i,"nameoff":nameoff,"off":off,"usize":usize,"csize":csize,"name":nm})
        return {"raw":bb,"magic":magic,"nf":nf,"tbl":tbl,"ntbl":ntbl,"dstart":dstart,"files":files}

    def rebuild_bundle(self, b, new_files):
        """새 번들 바이트 생성. new_files: {file_name:(stored,usize)}.
        ★원본 파일간 간격(gap/정렬) 보존 → 무변경 파일은 원위치, 변경 후만 델타 이동.
        무변경 번들이면 원본과 바이트 동일."""
        if b["nf"]==0:
            return bytearray(self._bundle_raw(b))
        info=self.parse_bundle_files(b)
        bb=info["raw"]; tbl=info["tbl"]
        files=info["files"]
        order=sorted(files,key=lambda f:f["off"])
        first_off=order[0]["off"]
        out=bytearray(bb[:first_off])   # 헤더+테이블+이름+선행패딩 보존
        prev_end=first_off; cur=first_off
        newvals={}  # idx -> (off,usize,csize)
        for f in order:
            if f["name"] in new_files:
                stored,usize=new_files[f["name"]]
            else:
                stored=bytes(bb[f["off"]:f["off"]+f["csize"]]); usize=f["usize"]
            gap=f["off"]-prev_end        # 원본 간격 보존(최소 밀림)
            if gap<0: gap=0
            cur+=gap
            if cur+len(stored)>len(out): out.extend(b"\x00"*(cur+len(stored)-len(out)))
            out[cur:cur+len(stored)]=stored
            newvals[f["idx"]]=(cur,usize,len(stored))
            prev_end=f["off"]+f["csize"]
            cur+=len(stored)
        for f in files:
            off,usize,csize=newvals[f["idx"]]
            struct.pack_into("<4I",out,tbl+16*f["idx"], f["nameoff"], off, usize, csize)
        return out

    def repack_minimal(self, new_files_by_bundle):
        """★최소 변경: 바뀐 번들만 원위치(원본 doff)에서 다시 씀. 나머지 번들·정렬 전부 불변.
        각 변경 번들은 원본 0x800 슬롯(다음 번들까지 거리) 안에 들어가야 함(초과 시 예외).
        반환 (out_bytes(TOTAL), 변경번들수)."""
        out=bytearray(self.data)
        new_sec1=bytearray(self.sec1)
        sd=sorted(self.bundles,key=lambda x:x["doff"])
        changed=0
        for i,b in enumerate(sd):
            ch=new_files_by_bundle.get(b["name"])
            if not ch: continue
            nb=self.rebuild_bundle(b,ch)
            next_doff=sd[i+1]["doff"] if i+1<len(sd) else TOTAL
            slot=next_doff-b["doff"]
            if len(nb)>slot:
                raise RuntimeError(f"번들 {b['name']} 슬롯초과 {len(nb)}>{slot} (재배치 필요)")
            out[b["doff"]:b["doff"]+len(nb)]=nb
            if len(nb)<b["dsize"]:
                for k in range(b["doff"]+len(nb), b["doff"]+b["dsize"]): out[k]=0
            nameoff=struct.unpack_from("<I",new_sec1,b["rec"])[0]
            struct.pack_into("<5I",new_sec1,b["rec"], nameoff, b["flags"], b["doff"], len(nb), b["nf"])
            changed+=1
        out[self.s1_off:self.s1_off+self.s1_size]=new_sec1
        return bytes(out), changed

    def repack(self, new_files_by_bundle):
        """new_files_by_bundle: {bundle_name:{file_name:(stored,usize)}} → (out_bytes, total_used)"""
        out=bytearray(self.data[:self.first_doff])  # 디렉토리 영역 보존
        new_sec1=bytearray(self.sec1)
        cur=self.first_doff
        for b in sorted(self.bundles,key=lambda x:x["doff"]):
            nf_changes=new_files_by_bundle.get(b["name"],{})
            nb=self.rebuild_bundle(b,nf_changes)
            cur=_align(cur,BUNDLE_ALIGN)
            if cur+len(nb)>len(out): out.extend(b"\x00"*(cur+len(nb)-len(out)))
            out[cur:cur+len(nb)]=nb
            struct.pack_into("<5I",new_sec1,b["rec"], *struct.unpack_from("<I",new_sec1,b["rec"]),  # nameoff 그대로
                             b["flags"], cur, len(nb), b["nf"])
            cur+=len(nb)
        used=cur
        # sec1 되쓰기
        out[self.s1_off:self.s1_off+self.s1_size]=new_sec1
        # 총 크기 맞춤
        if used<=TOTAL:
            out.extend(b"\x00"*(TOTAL-len(out)))
        return bytes(out[:max(used,TOTAL)]), used


if __name__=="__main__":
    import sys, io
    sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
    ISO=r"C:\Emul\Switch\패치유틸.xdeltaUI\Gundam Assault Survive (Japan).iso"
    fs=Fileset(ISO)
    print(f"번들 {fs.cnt}개, 첫 doff={fs.first_doff}, 디렉토리끝={fs.s2_off+fs.s2_size}")
    out,used=fs.repack({})   # 무변경 라운드트립
    print(f"재패킹 used={used} (원본 TOTAL={TOTAL}, 회수={TOTAL-used}), 출력크기={len(out)}")
    # 검증: 재패킹본을 새 Fileset처럼 파싱해 모든 파일 내용 원본과 동일한지
    import gaslib as G
    # 재패킹 out 을 임시로 파싱
    def parse_all(buf):
        s1o,s1s,s2o,s2s=struct.unpack_from("<4I",buf,0x18)
        sec1=buf[s1o:s1o+s1s]; sec2=buf[s2o:s2o+s2s]
        cnt=struct.unpack_from("<I",sec1,0)[0]; roffs=struct.unpack_from(f"<{cnt}I",sec1,4)
        res={}
        for i in range(cnt):
            no,fl,doff,dsize,nf=struct.unpack_from("<5I",sec1,roffs[i])
            e=sec2.index(b"\x00",no); bn=sec2[no:e].decode("ascii")
            if nf==0: continue
            bb=buf[doff:doff+dsize]
            m,n,tbl,ntbl,ds=struct.unpack_from("<4s4I",bb,0)
            for j in range(n):
                nao,off,us,cs=struct.unpack_from("<4I",bb,tbl+16*j)
                ee=bb.index(b"\x00",ntbl+nao); fn=bb[ntbl+nao:ee].decode("ascii")
                res[(bn,fn)]=bytes(bb[off:off+cs])
        return res
    orig=parse_all(bytes(fs.data)); new=parse_all(out)
    print("파일 수 orig",len(orig),"new",len(new))
    mism=[k for k in orig if orig[k]!=new.get(k)]
    print("불일치 파일:",len(mism))
    for k in mism[:10]: print("  ",k, len(orig[k]), len(new.get(k,b"")))
    print("라운드트립 OK" if not mism and len(orig)==len(new) else "라운드트립 실패")
