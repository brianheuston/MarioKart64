#!/usr/bin/env python3
# N64 ROM checksum recalculator (CIC-6102 / chksum64 algorithm).
import sys

CHECKSUM_START = 0x1000
CHECKSUM_LENGTH = 0x100000
CIC_6102 = 0xF8CA4DDC

M = 0xFFFFFFFF

def rol(i, b):
    return ((i << b) | (i >> (32 - b))) & M

def b2l(d, i):
    return (d[i] << 24) | (d[i+1] << 16) | (d[i+2] << 8) | d[i+3]

def calc_crc(data, seed=CIC_6102):
    t1 = t2 = t3 = t4 = t5 = t6 = seed
    i = CHECKSUM_START
    end = CHECKSUM_START + CHECKSUM_LENGTH
    while i < end:
        d = b2l(data, i)
        nt6 = (t6 + d) & M
        if nt6 < d:
            t4 = (t4 + 1) & M
        t6 = nt6
        t3 ^= d
        r = rol(d, d & 0x1F)
        t5 = (t5 + r) & M
        if t2 > d:
            t2 ^= r
        else:
            t2 ^= (t6 ^ d) & M
        t1 = (t1 + ((t5 ^ d) & M)) & M
        i += 4
    crc0 = (t6 ^ t4 ^ t3) & M
    crc1 = (t5 ^ t2 ^ t1) & M
    return crc0, crc1

def read_stored(data):
    return b2l(data, 0x10), b2l(data, 0x14)

def main():
    clean_path, target_path = sys.argv[1], sys.argv[2]
    with open(clean_path, "rb") as f:
        clean = bytearray(f.read())
    # --- self-validation against the known-good clean ROM ---
    c0, c1 = calc_crc(clean)
    s0, s1 = read_stored(clean)
    print(f"clean: computed {c0:08X} {c1:08X} | stored {s0:08X} {s1:08X} | "
          f"{'MATCH' if (c0, c1) == (s0, s1) else 'MISMATCH'}")
    if (c0, c1) != (s0, s1):
        print("ERROR: algorithm does not reproduce clean ROM CRC; aborting.")
        sys.exit(1)
    # --- compute + apply to the patched/target ROM ---
    with open(target_path, "rb") as f:
        rom = bytearray(f.read())
    t0, t1 = calc_crc(rom)
    o0, o1 = read_stored(rom)
    print(f"target: old {o0:08X} {o1:08X} -> new {t0:08X} {t1:08X}")
    if (t0, t1) == (o0, o1):
        print("target CRC already correct; nothing to do.")
        return
    rom[0x10:0x14] = t0.to_bytes(4, "big")
    rom[0x14:0x18] = t1.to_bytes(4, "big")
    with open(target_path, "wb") as f:
        f.write(rom)
    print(f"WROTE fixed CRC to {target_path}")

if __name__ == "__main__":
    main()
