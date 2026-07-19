"""Read-only PPSSPP process memory scan for the first situation title.

Used to detect stale save-state RAM restoring the original EBOOT string table.
"""
import ctypes
import ctypes.wintypes as wt
import json
import subprocess


PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wt.DWORD),
        ("PartitionId", wt.WORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wt.DWORD),
        ("Protect", wt.DWORD),
        ("Type", wt.DWORD),
    ]


def pids():
    cmd = [
        "powershell", "-NoProfile", "-Command",
        "(Get-Process PPSSPPWindows64 -ErrorAction SilentlyContinue).Id",
    ]
    return [int(x) for x in subprocess.check_output(cmd, text=True).split()]


def encoded_korean():
    stable = json.load(open("kr_map_stable.json", encoding="utf-8"))
    out = bytearray()
    for ch in "\uc2dc\uc791\uc758 \ud611\uace1":
        if ch == " ":
            out.append(0x20)
        else:
            out.extend(int(stable[ch][1]).to_bytes(2, "big"))
    return bytes(out)


def scan(pid, needles):
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.restype = wt.HANDLE
    k32.VirtualQueryEx.restype = ctypes.c_size_t
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        raise ctypes.WinError(ctypes.get_last_error())
    hits = {name: [] for name in needles}
    mbi = MEMORY_BASIC_INFORMATION()
    addr = 0
    max_addr = (1 << 47) - 1
    try:
        while addr < max_addr:
            got = k32.VirtualQueryEx(
                h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)
            )
            if not got:
                break
            base = int(mbi.BaseAddress or 0)
            size = int(mbi.RegionSize)
            readable = (
                mbi.State == MEM_COMMIT
                and not (mbi.Protect & PAGE_GUARD)
                and not (mbi.Protect & PAGE_NOACCESS)
            )
            if readable and size <= 512 * 1024 * 1024:
                buf = ctypes.create_string_buffer(size)
                nread = ctypes.c_size_t()
                if k32.ReadProcessMemory(
                    h, ctypes.c_void_p(base), buf, size, ctypes.byref(nread)
                ):
                    data = buf.raw[: nread.value]
                    for name, needle in needles.items():
                        start = 0
                        while True:
                            pos = data.find(needle, start)
                            if pos < 0:
                                break
                            hits[name].append(base + pos)
                            start = pos + 1
            addr = base + max(size, 0x1000)
    finally:
        k32.CloseHandle(h)
    return hits


if __name__ == "__main__":
    original = "\u306f\u3058\u307e\u308a\u306e\u5ce1\u8c37".encode("cp932")
    ko = encoded_korean()
    for pid in pids():
        result = scan(pid, {"original": original, "korean_donor": ko})
        print(f"PID {pid}")
        for name, addresses in result.items():
            print(f"  {name}: {len(addresses)} hits")
            for address in addresses[:20]:
                print(f"    0x{address:016x}")
