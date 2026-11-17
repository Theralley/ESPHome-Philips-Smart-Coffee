# Reflashing a Philips EP3243 (Series 3200 LatteGo) from a Mac

This folder belongs to a fork of
[ESPHome-Philips-Smart-Coffee](https://github.com/TillFleisch/ESPHome-Philips-Smart-Coffee).
It is a separate project inside that fork. The ESPHome component itself is unchanged.

## Status

| Step | State |
|---|---|
| Research: chips, programming route, Mac tools | Done (2026-11-17) |
| OpenOCD configs and a read-only dump script | Written; OpenOCD 0.12.0 parses them; not yet run on hardware |
| Photos and close-ups of the power board (labels, MCU, test points) | Done; see [Our boards](#our-boards) |
| Find the SWD pins on the power board with a continuity tester | To do |
| Close-ups of the UI board (label, MCU sticker) | To do |
| Raspberry Pi Pico W flashed with `debugprobe` and checked on the Mac | To do |
| Firmware check tools (`tools/fw_info.py`, `tools/crc_check.py`) | Written; tested on synthetic images |
| Forum account, download the firmware files | To do |
| Backup: read-only dumps of both boards plus the power board's EEPROM | To do |
| Replace all software: flash a matched MAIN and UI pair (an older version is accepted) | To do |
| Machine stops ghosting? If not, replace the power board | To do |

## Ground rules

1. **Normal components only.** No Philips Serkit SSC2 programmer and no Philips service cable.
2. **Everything runs on a Mac.**
3. **No licence or vendor accounts.** No Philips EPSC service-centre key, and no accounts for
   chip-vendor tools such as Infineon ModusToolbox or ST's STM32CubeProgrammer. **A forum
   account is fine** (changed 2026-11-17), so the firmware files on saeco-support-forum.de can
   be used.

These rules exclude Philips' official route (EPSC software, Serkit programmer, Windows and a
service centre key). The reasoning is in [DECISIONS.md](DECISIONS.md), and every source is
listed in [SOURCES.md](SOURCES.md).

## Why reflash

The machine "ghosts". Already done, without fixing it:

1. Cleaned the control panel, power-cycled, cleaned and greased the brew group, descaled.
2. Reseated the 8-pin ribbon cable between the mainboard and the UI board and checked the
   contacts.
3. Replaced the UI (display) board.

Replacing the UI board can itself cause strange behaviour. A repairer on the Saeco forum reports
that when the UI firmware does not match the mainboard firmware the machine may still run, but
it pauses for 30 seconds while heating. **Reading both firmware versions is therefore the first
diagnostic step, before anything is written.**

## Safety

- **Pull the mains plug for every step in this guide.** The board logic is not isolated from
  mains. The service manual says the board "is working at 230V" and that mains potential reaches
  all the way to the Philips programmer. Never connect a probe, the Mac or a logic analyser to the
  board while it is plugged in. With the back panel off, the mains terminals and the triac on its
  heatsink are exposed.
- **Power the board from a bench supply while programming:** 3.3 V, current limit 50 mA, on the
  board's `+5V` and `GND` test points. On our power board these are **TP11 (+5V)** and **TP14
  (GND)**, top left. Forum figures: the power board draws under 22 mA and the
  display under 26 mA at 5 V. Use 3.3 V because the Pico is a 3.3 V device and its pins are
  not 5 V tolerant. Both MCUs run at 3.3 V: the KE02 is specified for 2.7 to 5.5 V and the
  PSoC 4000S for 1.71 to 5.5 V.
- No bench supply: the Pico's `3V3(OUT)` pin can feed the board instead, but first measure
  between the board's `+5V` and `GND` with the multimeter. The forum's most common power-board
  fault is a short on that rail, and the Pico has no current limit to protect it.
- To program one board on its own, unplug the 8-wire UI ribbon cable. On our power board it
  plugs into the red Picoflex socket **JP9**. Pull gently and straight: two forum users tore off
  connector pins.

## The chips

| Board | MCU | Flash | OpenOCD target |
|---|---|---|---|
| Power board (mainboard) | NXP Kinetis **MKE02Z64VLD4** (Cortex-M0+, 44-LQFP) | 64 KB, plus 256 B EEPROM | `target/ke0x.cfg` (`kinetis_ke` driver) |
| UI board ("Omnia UI Basic") | Infineon/Cypress **CY8C4025AZI-S413** (PSoC 4000S, Cortex-M0+, 48-TQFP) | 32 KB | `target/psoc4.cfg` (`psoc4` driver) |

Sources: the Saeco forum thread, where one repairer reports about 25 machines from the 1200,
2200 and 3200 series, and the hackcorrelation teardown for the UI chip. According to the same
repairer, the power boards of the EP1200, EP2200, EP3200, EP4300 and EP5400 are identical apart
from the firmware. He has never found read-protected firmware on them. **Read the chip markings
on your own boards before buying anything.**

## Our boards

### Power board (photos and close-ups, 2026-11-17)

The photos are kept in `local/photos/` and are not published, because they carry GPS
positions in their metadata.

**Identity**

| What | Read from the board |
|---|---|
| PCB | `PHILIPS INNOVATIONS SPA 1.9.30.330.00 V11` |
| Barcode label on the green X2 capacitor, **crossed out with a marker** | `421945023121/02`, `SY22…093` |
| White label stuck over it | **`421945017971`** and **`V.01.05.02`** |
| Sticker on the MCU (U3) | **`V.01.01.05`** and **`CD2734BF`** |

Our reading, not yet verified:
- `421945023121` is the generic power board. Programming turned it into `421945017971` with
  software `V01.05.02`, which is why the old barcode is crossed out. The forum says the power
  boards are identical apart from the firmware, which fits.
- The MCU sticker shows an older version, `V01.01.05`. The chip was probably pre-programmed with
  it and updated to `V01.05.02` later, either at the end of the production line or by a service
  centre.
- `CD2734BF` looks like a 32-bit checksum of the firmware. After the dump,
  [`tools/crc_check.py`](tools/crc_check.py) tries to match it.
- **Our power board runs newer firmware than the forum files** (`v01.01` for the EP3246 and
  `v01.00.02` for the EP2235). Flashing those is a downgrade, **which we accept**: the fault
  survived every part swap, so the software is replaced before the power board is.

**Parts that matter for the reflash**

| Part | Where | Meaning |
|---|---|---|
| U3, 44-pin QFP under the sticker | Centre | The MCU. The pin count fits the MKE02Z64VLD4 (44-LQFP); OpenOCD reads the chip ID on connect |
| TP11 `+5V`, TP14 `GND` | Top left | Power for programming (3.3 V from the bench supply) |
| TP13 `U_TX`, TP12 `U_RX` | Top left, next to TP14 | A UART, probably the line to the UI board (it sits by the UI connector and U2) |
| **JP19**, 2 × 5 rectangular pads, unpopulated | Below left of U3 | **Candidate SWD port.** The layout matches the ARM 10-pin Cortex debug footprint |
| White 5-pin header, no cable | Left of R69 and R68 | **Candidate for the "white connector"** that the service manual reserves for the Philips programmer. It may carry SWD or a UART |
| JP9, red Picoflex socket | Top | The 8-wire UI ribbon cable |
| U2, small 8-pin IC | Next to JP9 | Fits the forum's NL27WZ17 RX/TX buffer |
| Q9, SOT-23 | Next to DL3 | Fits the forum's FDN304 P-MOSFET for the sensor supply |
| Glass fuse `T1A L 250V` | Bottom left | The 1 A slow fuse the forum mentions |
| Mains terminals N, ⏚, L (JP4, JP3) | Bottom | Mains input. **Plug out!** |

**Finding the SWD pins (machine unplugged, multimeter in continuity mode)**

According to the NXP KE02 data sheet, on the 44-LQFP package **pin 42 = PTC4 = SWD_CLK** and
**pin 44 = PTA4 = SWD_DIO**. Both sit at the pin 1 corner: pin 1 is marked with a dot, pins are
numbered anticlockwise, so 44 is next to pin 1. Also find **RESET_b (PTA5)** in the data sheet's
44-LQFP table.

1. Check which JP19 pads and which pins of the white 5-pin header connect to U3 pins 42 and 44,
   to RESET_b, to TP11 (+5V) and to TP14 (GND).
2. If the white header carries all five, a matching 5-pin plug or jumper wires are enough and
   nothing needs soldering. Otherwise solder five thin wires to JP19.
3. The forum's pinout photos (`pinout.jpg`, `disp-swd-pinout.jpg`) can be checked against this
   once the forum account exists.

### UI board

Replaced as part of the fault-finding. Its label (UI 12NC and version) and the sticker on its
PSoC are still to be photographed. They show whether its firmware matches the power board's
`V01.05.02`.

## Hardware (all off the shelf)

| Item | Why |
|---|---|
| **Raspberry Pi Pico W (RP2040), which we have** | SWD probe (CMSIS-DAP) with Raspberry Pi's `debugprobe` firmware, works with OpenOCD on macOS |
| Bench power supply with current limit | 3.3 V to the board being programmed |
| Thin wire and a soldering iron, or a pogo-pin clip | Five wires to the SWD header on each board |
| Multimeter | Continuity checks to identify the SWD pins; check the 5 V rail for shorts |
| Torx T10 | Back panel |

Alternative probe: a SEGGER J-Link EDU Mini, which forum members have used on exactly these
boards. Its software needs no account, but its licence covers non-commercial use only. Avoid
J-Link clones such as "V9" boards from AliExpress. They run copied SEGGER firmware with
unlicensed keys, and SEGGER's software can disable them during an update.

## Software on the Mac (no accounts)

```sh
brew install open-ocd      # OpenOCD 0.12.0; ships target/ke0x.cfg and target/psoc4.cfg
brew install srecord       # optional: hex/bin conversion (srec_cat)
```

### Turning the Pico W into a probe

Raspberry Pi publishes no `debugprobe` build for the Pico W (see debugprobe issues
[#41](https://github.com/raspberrypi/debugprobe/issues/41) and
[#160](https://github.com/raspberrypi/debugprobe/issues/160)). The plain Pico build should still
work: SWD uses GP2 and GP3, which are the same on the Pico W. The firmware's LED pin GP25 goes
to the Pico W's Wi-Fi chip instead of an LED, so **the LED stays dark**. That is expected.

1. Download `debugprobe_on_pico.uf2` from
   [raspberrypi/debugprobe releases](https://github.com/raspberrypi/debugprobe/releases)
   (v2.3.1 at the time of writing).
2. Hold BOOTSEL, plug the Pico W into the Mac, and copy the file to the `RPI-RP2` drive.
3. Check that the Mac sees a CMSIS-DAP probe:
   `system_profiler SPUSBDataType | grep -i -B2 -A6 cmsis-dap`
4. If it does not show up, build debugprobe from source with `-DPICO_BOARD=pico_w`, as the
   maintainer suggests in #41. If that fails too, a plain Pico costs a few euros.

Pico wiring, from `include/board_pico_config.h` in debugprobe: **GP2 = SWCLK, GP3 = SWDIO,
GP1 = RESET**, plus GND. Leave the Pico's 3V3 and VSYS unconnected when a bench supply powers
the target.

## Plan

### Step 0: two free resets (service manual pp. 30 and 40)

- **Steam-Out** resets all machine parameters to factory values. Unplug the machine. Plug it back
  in, then within 2 seconds press **B4, B2, B5, B3** (an "S"). The dreg drawer must be in place
  and the service door closed. When L25 and L26 light up, it is done.
- **Test mode, level 0** clears the error log. Within 2 seconds of plugging in, press
  **B5, B2, B4, B3**, then hold **B3** for 3 seconds. Level 1 tests every button and LED, and
  level 2 tests the loads and sensors (press B1 to change level).

### Step 1 (optional): find out which board sends the ghost

The UART traffic between the boards (115200 baud, pins 4 and 5 of the ribbon cable, see the
main README) shows whether a "button press" really comes from the UI board. This has to happen
while the machine is on mains, so **do not wire a logic analyser to the Mac**: its ground would
sit at mains potential. Use an ESP that only listens, powered by the machine and logging over
Wi-Fi: ESPHome with two `uart` blocks that have only an `rx_pin` and `debug: direction: RX`. The
bus is driven at 5 V, so put a resistor divider (for example 10 kΩ over 20 kΩ) in front of each
ESP input. A press that appears on the display-to-mainboard line without anyone touching the
panel points at the UI board. A machine that acts without such a message points at the
mainboard.

### Step 2: open up and identify

1. Unplug the machine and remove the back panel (2 × T10 at the bottom). The power board sits
   behind it.
2. Take close-ups (see the table above). Write down the **MAIN** and **UI** 12NC labels (for
   example `MAIN 421945020851`, `UI 421945020831`), the chip markings and the machine's 12NC and
   serial number.
3. Find the SWD pins on each board. For the power board, see
   [Finding the SWD pins](#our-boards): JP19 or the white 5-pin header. Confirm each pin with the
   continuity tester: GND, +5V, and the MCU's SWD data, SWD clock and reset pins.
   - KE02 (44-LQFP): `SWD_CLK` = pin 42 (PTC4), `SWD_DIO` = pin 44 (PTA4). Look up `RESET_b`
     (PTA5) in the data sheet's 44-LQFP table.
   - PSoC 4000S: `SWDIO` = P3.2, `SWDCLK` = P3.3, and `XRES`. This is the usual PSoC 4
     assignment; confirm it in the CY8C4025 data sheet's pin table.

### Step 3: wire up

Mains plug out. Unplug the UI ribbon cable from JP9. Connect the bench supply (3.3 V, 50 mA)
to the `+5V` and `GND` test points of the board you are working on (power board: TP11 and TP14). Pico GP2 goes to SWCLK, GP3
to SWDIO, GP1 to RESET (XRES on the UI board) and GND to GND.

### Step 4: dump (read-only, always first)

```sh
cd reflash-ep3243/openocd
./dump.sh main     # power board
./dump.sh ui       # UI board
```

Each run reads the flash three times into `reflash-ep3243/local/dumps/` and compares the
SHA-256 sums. Three identical reads mean the wiring is good. For the power board it also saves
the 256-byte EEPROM at `0x10000000` (machine parameters). That copy is for reference only:
OpenOCD cannot write it back, and Steam-Out resets the parameters anyway. **These dumps are the
way back if the new software makes things worse.** **If OpenOCD reports the KE02 as
secured or the PSoC as `PROTECTED`, stop.** Unlocking erases the chip. Do it only once a
matching replacement image is on disk.

With a J-Link EDU Mini instead, the forum procedure in J-Link Commander (`JLinkExe`) is:
`connect`, choose the device, `S` for SWD, speed `400`, then
`savebin <file> 0x0 0x10000` for the power board (64 KB) or `0x8000` for the UI board (32 KB).

### Step 5: find the versions

```sh
strings -n 6 ../local/dumps/main-*-1.bin | grep -i -E 'v?[0-9]{2}\.[0-9]{2}(\.[0-9]{2})?'
```

Then check the dump against the MCU sticker's checksum:

```sh
python3 -I ../tools/crc_check.py ../local/dumps/main-<stamp>-1.bin CD2734BF
```

A match means the chip still holds `V01.01.05`, the version on the MCU sticker. No match proves
nothing, because the checksum algorithm is a guess.

Firmware file names on the forum follow the pattern
`main_421941311961_v01.00.02_ep2235.hex` and
`control_panel_421941311861.03_v00.00.01_ep2235.hex`: board 12NC plus version. Compare the
mainboard and UI versions with each other. Whether the version strings are actually stored in
the image is not yet confirmed.

### Step 6: choose the new software

**Strategy (decided 2026-11-17): replace all software before replacing the power board.** The
fault survived every part swap, so what is left is the power board itself or its software. An
older firmware version is acceptable.

1. **Use a matched pair.** Flash MAIN and UI from the same set and never mix families, because a
   mismatch is a known cause of odd behaviour. Thread 65595 on the forum (needs an account) has:
   - `421941311901.04_v01.01_EP3246.zip`, which a repairer posted as the firmware for the EP3200
     series. The EP3246 is the EP3243's LatteGo sibling. Check whether it holds both a MAIN and a
     UI image.
   - `control_panel_421941311861.03_v00.00.01_ep2235.zip`, a UI image for the EP2200 series
     (`421941311861` revisions `.03` and `.04` are compatible, according to the same repairer).
2. **Check the UI image against our UI board's label** (still to be photographed). If the set has
   no UI image that fits, ask in the thread.
3. **Inspect every file before it is flashed:**

   ```sh
   python3 -I ../tools/fw_info.py --chip ke02  ../local/firmware/<main>.hex --compare ../local/dumps/main-<stamp>-1.bin --out ../local/firmware/main.bin
   python3 -I ../tools/fw_info.py --chip psoc4 ../local/firmware/<ui>.hex   --compare ../local/dumps/ui-<stamp>-1.bin   --out ../local/firmware/ui.bin
   ```

   The tool prints the address ranges, a sane vector table, version strings, how much differs
   from our dump and, for the KE02, the security byte. **It exits with 1 and "DO NOT FLASH"** if
   the vector table is wrong or the KE02 security byte would lock the debug port. `--out` writes
   a clean binary covering just the flash range, which is what gets flashed in step 7. PSoC
   Creator hex files carry extra data above `0x90000000`, and that data is left out.
4. Other sources, if the forum set does not fit: a **donor board** with the same 12NC, dumped in the
   same way, or as a last resort **our own dumps** (that only helps against corrupted flash).

Keep the files in `local/firmware/`. They are Philips' firmware and must never be committed to
this public fork; `.gitignore` blocks `*.hex`, `*.bin` and `*.zip`.

### Step 7: flash both boards

Flash the binaries that `fw_info.py --out` wrote, one board at a time. Each board is powered on
its own and the ribbon cable is unplugged.

```sh
openocd -f main-ke02.cfg -c "program ../local/firmware/main.bin 0x0 verify reset exit"
openocd -f ui-psoc4.cfg  -c "program ../local/firmware/ui.bin 0x0 verify reset exit"
```

`verify` reads the flash back and compares it with the file. Afterwards, dump the board again
with `dump.sh` and compare with `fw_info.py --compare` to make sure it holds the new image.

About the KE02's security byte (`0x40E`, reference manual table 18-6): if it is set to "secured",
the chip still runs, but the debug port can no longer read or write it. The only way back is a
mass erase over SWD (`kinetis_ke mdm mass_erase`), which wipes the chip, followed by flashing
again. `fw_info.py` blocks such images.

**Way back:** flash our own dumps from step 4 in the same way. The EEPROM copy cannot be
written back; Steam-Out resets the parameters instead.

With J-Link Commander: `loadfile <file.hex>`, then `r`, `g`, `q`. The file path must not
contain spaces (forum).

### Step 8: back together and test

Plug the ribbon cable back in and close the machine. Then run Steam-Out (step 0), because older
firmware may read the EEPROM parameters differently, and test mode level 1 and 2. Use the
machine as usual and note whether the fault comes back.

### Step 9: if the fault stays

If the fault remains with fresh software on both boards, the power board's hardware is what is
left. Replace the board. The forum puts a new power board at about 60 euros and says new boards
come pre-programmed, but check that its version matches the UI board. Our dumps make it possible
to compare the old and new board's software.

## Known failure parts (forum reports, not verified)

- **Power board:** the 1 A fuse, the boiler triac BTA312 and the transistor next to it, the MCU,
  the P-channel MOSFET Q9 (FDN304, which switches the sensor supply on for about 5 s after
  power-up), the logic buffer NL27WZ17 on the RX/TX lines (U2), and 1 kΩ resistors. When the
  fuse blows, mains can reach the 5 V rail and take out everything on it: both MCUs, the water
  level hall sensor, the flowmeter and the NTC.
- **UI board:** the MCU. On the 1200, 2200 and 3200 series the PSoC runs straight from 5 V with
  no regulator.
- The service manual's test tables name a "uP U2 in Main", while a forum post calls U2 the
  NL27WZ17 buffer. On our V11 board the MCU is U3, and U2 is a small 8-pin IC by the UI
  connector, which fits the forum's version.

## Open questions

- Which of JP19 and the white 5-pin header carries SWD. Answered by the continuity test.
- What the UI board's label and version say, and whether they match `V01.05.02`.
- Whether `CD2734BF` is a CRC of the firmware.
- Where the machine parameters live. `flash read_bank` does not read the KE02's 256-byte
  EEPROM. Steam-Out resets the parameters either way.
