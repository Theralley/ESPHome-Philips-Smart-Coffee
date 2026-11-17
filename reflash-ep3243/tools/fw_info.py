#!/usr/bin/env python3
"""Inspect a firmware image (.hex or .bin) before it goes anywhere near a chip.

Usage:
  python3 -I fw_info.py --chip ke02|psoc4 <image.hex|image.bin> [--compare dump.bin] [--out flash.bin]

Reports:
  - the address ranges in the file and anything outside the chip's flash
  - SHA-256 of the flash image (padded with 0xFF to the full flash size)
  - whether the vector table looks sane (stack pointer in RAM, reset vector in flash)
  - KE02 only: the flash configuration field at 0x400-0x40F, above all the security byte
  - version-like strings
  - with --compare: how many bytes differ from a dump, and where
  - with --out: writes the padded flash image as .bin, for comparing or flashing

Exit code 0 = no blocking problem found, 1 = a blocking problem (do not flash), 2 = usage.
"""
import argparse
import hashlib
import re
import sys

CHIPS = {
    # flash size, RAM range (inclusive start, exclusive end) for the initial stack pointer
    "ke02": {"flash": 64 * 1024, "ram": (0x1FFFFC00, 0x20000C00)},
    "psoc4": {"flash": 32 * 1024, "ram": (0x20000000, 0x20001000)},
}


def read_intel_hex(path):
    """Return {address: byte} from an Intel HEX file. Raises ValueError on bad records."""
    mem = {}
    base = 0
    with open(path, "r", encoding="ascii", errors="strict") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            if not line.startswith(":"):
                raise ValueError(f"line {lineno}: not an Intel HEX record")
            raw = bytes.fromhex(line[1:])
            if len(raw) < 5 or len(raw) != raw[0] + 5:
                raise ValueError(f"line {lineno}: bad record length")
            if sum(raw) & 0xFF:
                raise ValueError(f"line {lineno}: bad checksum")
            count, addr, rtype, data = raw[0], (raw[1] << 8) | raw[2], raw[3], raw[4:-1]
            if rtype == 0x00:
                for i, b in enumerate(data):
                    mem[base + addr + i] = b
            elif rtype == 0x01:
                break
            elif rtype == 0x02:
                base = int.from_bytes(data, "big") << 4
            elif rtype == 0x04:
                base = int.from_bytes(data, "big") << 16
            elif rtype in (0x03, 0x05):
                pass  # start address records: not needed here
            else:
                raise ValueError(f"line {lineno}: unknown record type {rtype:#04x}")
    return mem


def segments(addresses):
    out = []
    for a in sorted(addresses):
        if out and a == out[-1][1]:
            out[-1][1] = a + 1
        else:
            out.append([a, a + 1])
    return out


def load(path, flash_size):
    """Return (flash image padded with 0xFF, list of segments, bytes outside flash)."""
    if path.lower().endswith((".hex", ".ihex")):
        mem = read_intel_hex(path)
    else:
        with open(path, "rb") as f:
            mem = dict(enumerate(f.read()))
    image = bytearray(b"\xff" * flash_size)
    outside = 0
    for addr, b in mem.items():
        if addr < flash_size:
            image[addr] = b
        else:
            outside += 1
    return bytes(image), segments(mem.keys()), outside


def word(image, offset):
    return int.from_bytes(image[offset:offset + 4], "little")


def main(argv):
    p = argparse.ArgumentParser(add_help=True, description="Inspect a firmware image.")
    p.add_argument("--chip", required=True, choices=sorted(CHIPS))
    p.add_argument("image")
    p.add_argument("--compare")
    p.add_argument("--out")
    try:
        args = p.parse_args(argv[1:])
    except SystemExit:
        return 2

    chip = CHIPS[args.chip]
    blocking = []
    try:
        image, segs, outside = load(args.image, chip["flash"])
    except (OSError, ValueError, UnicodeDecodeError) as e:
        print(f"Cannot read {args.image}: {e}")
        return 1

    print(f"File: {args.image}")
    print(f"Chip: {args.chip}, flash {chip['flash'] // 1024} KB")
    print("Address ranges in the file:")
    for start, stop in segs:
        where = "" if stop <= chip["flash"] else "   <- outside flash"
        print(f"  0x{start:08X}-0x{stop - 1:08X} ({stop - start} bytes){where}")
    if outside:
        print(f"Note: {outside} bytes lie outside flash and are not part of the image below.")
        print("      (PSoC Creator hex files keep checksum, protection and metadata there.)")

    used = len(image.rstrip(b"\xff"))
    print(f"Used flash: {used} bytes ({used * 100 // chip['flash']} %)")
    print(f"SHA-256 of padded flash image: {hashlib.sha256(image).hexdigest()}")

    sp, reset = word(image, 0), word(image, 4)
    ram_lo, ram_hi = chip["ram"]
    sp_ok = ram_lo < sp <= ram_hi
    reset_ok = (reset & 1) == 1 and (reset & ~1) < chip["flash"]
    print(f"Initial stack pointer: 0x{sp:08X} {'ok' if sp_ok else 'NOT IN RAM'}")
    print(f"Reset vector:          0x{reset:08X} {'ok' if reset_ok else 'NOT A THUMB ADDRESS IN FLASH'}")
    if not (sp_ok and reset_ok):
        blocking.append("vector table does not look like this chip")

    if args.chip == "ke02":
        # KE02 reference manual, table 18-6: 0x400-0x407 backdoor key, 0x408-0x40B reserved (0xFF),
        # 0x40C EEPROM protection, 0x40D flash protection, 0x40E flash security, 0x40F nonvolatile.
        cfg = image[0x400:0x410]
        print("Flash configuration field 0x400-0x40F: " + cfg.hex(" ").upper())
        fsec = cfg[0x0E]
        sec, keyen = fsec & 0x03, (fsec >> 6) & 0x03
        print(f"  Security byte 0x40E = 0x{fsec:02X}: SEC={sec:02b} "
              f"({'unsecured' if sec == 0b10 else 'SECURED'}), KEYEN={keyen:02b}")
        print(f"  Flash protection 0x40D = 0x{cfg[0x0D]:02X}, EEPROM protection 0x40C = 0x{cfg[0x0C]:02X}")
        if sec != 0b10:
            blocking.append("security byte 0x40E would lock the debug port after flashing "
                            "(recoverable only by a mass erase, which wipes the chip)")
        if cfg[0x08:0x0C] != b"\xff\xff\xff\xff":
            print("  Warning: reserved bytes 0x408-0x40B are not 0xFF.")

    found = sorted(set(re.findall(rb"[Vv]?\.?\d{1,2}\.\d{2}(?:\.\d{2}){0,2}", image)))
    if found:
        print("Version-like strings: " + ", ".join(s.decode("ascii") for s in found[:20]))
    else:
        print("Version-like strings: none found")

    if args.compare:
        try:
            other, _, _ = load(args.compare, chip["flash"])
        except (OSError, ValueError, UnicodeDecodeError) as e:
            print(f"Cannot read {args.compare}: {e}")
            return 1
        diff = [i for i in range(chip["flash"]) if image[i] != other[i]]
        if not diff:
            print(f"Compared with {args.compare}: identical.")
        else:
            ranges = segments(diff)
            print(f"Compared with {args.compare}: {len(diff)} bytes differ in {len(ranges)} ranges.")
            for start, stop in ranges[:10]:
                print(f"  0x{start:05X}-0x{stop - 1:05X}")
            if len(ranges) > 10:
                print(f"  ... and {len(ranges) - 10} more")

    if args.out:
        with open(args.out, "wb") as f:
            f.write(image)
        print(f"Wrote padded flash image to {args.out}")

    if blocking:
        print("DO NOT FLASH:")
        for b in blocking:
            print(f"  - {b}")
        return 1
    print("No blocking problem found.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
