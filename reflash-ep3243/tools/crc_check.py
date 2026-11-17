#!/usr/bin/env python3
"""Check a flash dump against the 32-bit value printed on the MCU sticker.

Usage: python3 -I crc_check.py <dump.bin> <hex value, e.g. CD2734BF>

The power board's MCU sticker reads "V.01.01.05" and "CD2734BF". The second line
looks like a 32-bit checksum of the firmware, but the algorithm is not known. This
script tries standard CRC-32 (zlib) over a few plausible ranges, and also looks
for the value stored inside the image. A match tells which firmware is on the
chip. No match proves nothing, because the algorithm is only a guess.
"""
import sys
import zlib


def ranges(data):
    end = len(data)
    used = len(data.rstrip(b"\xff"))
    yield "whole image", 0, end
    yield "up to last non-0xFF byte", 0, used
    yield "up to last non-0xFF byte, minus 4", 0, used - 4
    # On Kinetis parts the flash configuration field sits at 0x400-0x40F.
    yield "0x410 to end", 0x410, end
    yield "0x410 to last non-0xFF byte", 0x410, used


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    with open(argv[1], "rb") as f:
        data = f.read()
    want = int(argv[2], 16)
    hit = False

    for name, start, stop in ranges(data):
        if stop <= start:
            continue
        crc = zlib.crc32(data[start:stop]) & 0xFFFFFFFF
        for label, value in (("CRC-32", crc), ("CRC-32, inverted", crc ^ 0xFFFFFFFF)):
            match = value == want
            hit = hit or match
            mark = "MATCH" if match else "     "
            print(f"{mark} {label:17} {name:34} 0x{start:05X}-0x{stop:05X} = {value:08X}")

    for order in ("little", "big"):
        pos = data.find(want.to_bytes(4, order))
        if pos >= 0:
            hit = True
            print(f"MATCH value stored in the image ({order}-endian) at 0x{pos:05X}")

    if hit:
        print("At least one match.")
    else:
        print("No match. The dump may still be fine: the algorithm is a guess.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
