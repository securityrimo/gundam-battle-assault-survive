# -*- coding: utf-8 -*-
"""순수 파이썬 PSP ~PSP PRX 복호화 (type2, tag 0xD91612F0).
pspdecrypt(John-K) PrxDecrypter.cpp + libkirk 를 충실히 포팅.
KIRK: kirk7 = AES-128-CBC(IV=0, key=keyvault[keyId]);
      CMD1 = 마스터키로 헤더 0x20 복호→bodyAES, 본문 CBC 복호.
무결성 검증(SHA1/CMAC/ECDSA)은 복호화에 불필요하므로 생략."""
import struct, zlib, sys
from Crypto.Cipher import AES
from gas_keys import KEYVAULT, KIRK1_KEY, KEY_D91612F0

def cbc_dec(key, data):
    # AES-128-CBC, IV=0 (KIRK AES_cbc_decrypt 동작과 동일)
    return AES.new(key, AES.MODE_CBC, b"\x00"*16).decrypt(data)

def kirk7(data, keyId):
    return cbc_dec(KEYVAULT[keyId], data)

def expand_seed(seed16, code):
    buf=bytearray(0x90)
    for i in range(0,0x90,0x10):
        buf[i:i+0x10]=seed16
        buf[i]=i//0x10
    return bytearray(kirk7(bytes(buf), code))

def decrypt_kirk_header(kirk_header, xorbuf, code):
    # xorbuf 는 expand_seed 결과. offset 0x10 부터 사용.
    tmp=bytearray(0x40)
    for i in range(0x40):
        tmp[i]=kirk_header[i]^xorbuf[0x10+i]
    tmp=bytearray(kirk7(bytes(tmp),code))
    for i in range(0x40):
        tmp[i]^=xorbuf[0x50+i]
    return tmp

def kirk_cmd1(cmd1_in):
    # cmd1_in: 0x90 헤더 + 본문
    keys=cbc_dec(KIRK1_KEY, cmd1_in[:0x20])
    body_aes=keys[:0x10]
    data_size=struct.unpack_from("<I",cmd1_in,0x70)[0]
    data_offset=struct.unpack_from("<I",cmd1_in,0x74)[0]
    src=cmd1_in[0x90+data_offset:0x90+data_offset+data_size]
    if len(src)%16: src=src+b"\x00"*(16-len(src)%16)
    return cbc_dec(body_aes, src)[:data_size]

def decrypt_type2(inbuf):
    tag=struct.unpack_from("<I",inbuf,0xD0)[0]
    assert tag==0xD91612F0, hex(tag)
    code=0x5D
    decrypt_size=struct.unpack_from("<i",inbuf,0xB0)[0]

    xorbuf=expand_seed(KEY_D91612F0, code)

    # PRXType2 필드 추출
    id_       = inbuf[0x140:0x150]      # 0x10
    sha1      = inbuf[0x12C:0x140]      # 0x14
    kirk_hdr  = inbuf[0x80:0xB0]+inbuf[0xC0:0xD0]   # 0x40
    kirk_meta = inbuf[0xB0:0xC0]        # 0x10
    prx_hdr   = inbuf[0x00:0x80]        # 0x80

    # type2.decrypt: kirk7(id, 0x60) over 연속 [id|sha1|kirk_hdr|kirk_meta]
    blk=bytearray(id_+sha1+kirk_hdr+kirk_meta)   # 0x74
    blk[:0x60]=kirk7(bytes(blk[:0x60]), code)
    id_=bytes(blk[0x00:0x10]); sha1=bytes(blk[0x10:0x24])
    kirk_hdr=bytes(blk[0x24:0x64]); kirk_meta=bytes(blk[0x64:0x74])

    # KIRK_CMD1_HEADER (0x90) 구성
    header=bytearray(0x90)
    header[0x70:0x80]=kirk_meta            # data_size@0x70, data_offset@0x74
    hk=decrypt_kirk_header(kirk_hdr, xorbuf, code)
    header[0:0x40]=hk
    struct.pack_into("<I",header,0x60,1)   # mode=1
    # ecdsa_hash@0x64 = 0

    cmd1_in=bytes(header)+prx_hdr+inbuf[0x150:]
    out=kirk_cmd1(cmd1_in)
    return out[:decrypt_size], decrypt_size

def maybe_decompress(data):
    if data[:4]==b"\x7fELF":
        return data, "elf"
    if data[:2]==b"\x1f\x8b":
        # gzip
        return zlib.decompress(data, 16+15), "gzip"
    if data[:4]==b"2RLZ":
        return None, "2RLZ(미지원)"
    if data[:4]==b"KL4E" or data[:4]==b"KL3E":
        return None, "KL4E(미지원)"
    return data, "raw?"

if __name__=="__main__":
    enc=open(r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas\EBOOT_enc.bin","rb").read()
    print("size",len(enc),"tag@D0",enc[0xD0:0xD4].hex())
    dec,ds=decrypt_type2(enc)
    print("decrypt_size(0xB0)=",ds,"decrypted head=",dec[:16].hex())
    body,kind=maybe_decompress(dec)
    print("payload kind:",kind)
    if body is not None:
        print("payload head:",body[:16].hex(), "size",len(body))
        outp=r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas\EBOOT_dec.elf"
        open(outp,"wb").write(body)
        print("wrote",outp)
        # ELF 확인
        if body[:4]==b"\x7fELF":
            e_type=struct.unpack_from("<H",body,0x10)[0]
            e_machine=struct.unpack_from("<H",body,0x12)[0]
            print("ELF! e_type=%d e_machine=%d (8=MIPS)"%(e_type,e_machine))
    else:
        # 압축 미지원이면 복호 원본이라도 저장
        open(r"C:\Emul\Switch\패치유틸.xdeltaUI\work_gas\EBOOT_dec_raw.bin","wb").write(dec)
        print("wrote raw decrypted (compressed) payload")
