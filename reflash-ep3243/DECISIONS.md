# Decisions

## 2026-11-17, late: replace all software first, an older version is fine

- **The owner accepts a lower firmware version.** The fault survives every part swap, so only
  the power board or its software is left. **Strategy: replace all software on both boards
  before replacing the power board.** This supersedes the evening decision not to flash the
  forum files to the power board.
- MAIN and UI are flashed as a **matched pair from the same set**. Before anything is written,
  both boards are dumped, along with the KE02 EEPROM. Those dumps are the way back.
- `tools/fw_info.py` inspects every image before it is flashed: address ranges, vector table,
  KE02 security byte, a comparison with our dump, and a clean `.bin` for the flash range. It was
  tested on synthetic images only.
- Corrected after reading the KE02 reference manual (table 18-6, section 8.2): the security byte
  is `0x40E`. A secured KE02 can always be mass-erased over SWD, so it is **not** locked for good.
  The README said otherwise before.
- If the fault survives fresh software, the power board is replaced.
- `local/STATE.md` (gitignored) keeps the private working state: inventory, checksums and the
  next steps.

## 2026-11-17, evening: what the power board close-ups changed

- **The power board's firmware is `V01.05.02`** (label `421945017971`), which is newer than both
  forum main images. **Decision: the forum files are not flashed to the power board.** For the
  power board, our own dump is the reference. The forum files stay relevant for the UI board.
- The MCU sticker reads `V.01.01.05` and `CD2734BF`. `tools/crc_check.py` was added to test
  whether `CD2734BF` is a CRC of the dump. It was tested on a synthetic image only.
- Programming power: TP11 (+5V) and TP14 (GND). SWD candidates: the JP19 pads or the white
  5-pin header. This is decided by continuity tests to U3 pins 42 (SWD_CLK) and 44 (SWD_DIO).
- Next: the continuity test, UI board close-ups, and setting up the Pico W.

## 2026-11-17, later: rule 3 narrowed, Pico W as the probe

- **Rule 3 is now "no licence or vendor accounts".** A forum account is allowed. Not allowed are
  accounts such as the Philips EPSC service-centre key, Infineon (ModusToolbox) or ST
  (STM32CubeProgrammer). As a result, the forum firmware files in thread 65595 become the
  preferred source of a matching image. Our own dumps are still taken first, as a backup.
- **Probe: the Raspberry Pi Pico W (RP2040) we already have**, flashed with the plain Pico build
  of `debugprobe`. There is no official Pico W build, and the LED stays dark. Fallbacks: build
  with `-DPICO_BOARD=pico_w`, or buy a plain Pico.
- **The fork's top-level README now opens with what this fork does and how far it has got**, so
  that visitors see it before the upstream text.
- Overview photos of the power board were taken. They are kept in `local/photos/`, unpublished,
  until it is decided whether to publish them (EXIF data checked first).

## 2026-11-17

**Machine:** Philips Series 3200 LatteGo, EP3243 (probably /50).

**Problem:** the machine "ghosts". Cleaning, the brew group, reseating the ribbon cable and
replacing the UI board did not help. The owner chose to reflash.

**Ground rules set by the owner:**

1. Normal components only.
2. Everything runs on a Mac.
3. No registration.

### Rejected

| Option | Why rejected |
|---|---|
| Philips EPSC with Serkit SSC2 `996530009845` and cable `421946047151` | Breaks all three rules: Philips-only hardware, Windows only (Vista to 10, .NET), and a registration that issues a Service Center Key. It is otherwise the cleanest route, because EPSC picks the right MAIN and UI images from the serial number |
| A plain USB-UART adapter on the mainboard's white programming connector with the machine on mains | The board logic is at mains potential. Nothing is ever connected to the board while it is plugged in |
| Firmware attachments on saeco-support-forum.de | Rule 3. The attachments return HTTP 403 without a login. *Reversed later the same day: a forum account is allowed (see above).* |
| J-Link clones ("V9" and similar) | They run copied SEGGER firmware with unlicensed keys, and SEGGER's software can disable them |
| A wired logic analyser on the running machine | Its ground would be at mains potential. A listen-only ESP on Wi-Fi is used instead |

### Chosen

- **Probe:** a Raspberry Pi Pico with `debugprobe` (CMSIS-DAP) and OpenOCD from Homebrew.
  Fully open and needs no account. Fallback: a SEGGER J-Link EDU Mini with J-Link Commander,
  which forum users have used on these exact boards (non-commercial licence).
- **Power while programming:** a bench supply at 3.3 V with a 50 mA limit on the board's
  test points, with the mains plug out.
- **Firmware source:** only our own dumps, plus dumps from a donor board with the same 12NC.
- **Order:** the free resets (Steam-Out and clearing the error log), an optional check of which
  board sends the ghost, then dump both boards read-only and compare the versions. Write only
  after that.
- **Publication:** this is a public fork. No Philips documents, forum content, firmware or dumps
  go into git. They live in `local/`, which is gitignored.

### Earlier findings that led here

- The ESPHome project upstream supports the EP3243 but leaves the Philips firmware alone. It is
  a useful tool for watching the bus, not a fix.
- The Philips service manual describes the board as working at 230 V and lists the official
  programming kit.
