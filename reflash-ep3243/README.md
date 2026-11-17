# Reflashing a Philips EP3243 (Series 3200 LatteGo) from a Mac

This folder belongs to a fork of
[ESPHome-Philips-Smart-Coffee](https://github.com/TillFleisch/ESPHome-Philips-Smart-Coffee).
It is a separate project inside that fork. The ESPHome component itself is unchanged.

## Status

| Step | State |
|---|---|
| Research: chips, programming route, Mac tools | Done (2026-11-17) |
| OpenOCD configs and a read-only dump script | Written; OpenOCD 0.12.0 parses them; not yet run on hardware |
| Overview photos of the power board | Taken (kept locally) |
| Close-ups: board labels, chip markings, SWD header | To do |
| Raspberry Pi Pico W flashed with `debugprobe` and checked on the Mac | To do |
| Forum account, download the matching firmware | To do |
| Read-only dumps of both boards, compare versions | To do |
| Flash a matching MAIN and UI pair | To do |
| Machine stops ghosting | To do |

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
  board's `+5V` and `GND` test points. Forum figures: the power board draws under 22 mA and the
  display under 26 mA at 5 V. Use 3.3 V because the Pico is a 3.3 V device and its pins are
  not 5 V tolerant. Both MCUs run at 3.3 V: the KE02 is specified for 2.7 to 5.5 V and the
  PSoC 4000S for 1.71 to 5.5 V.
- No bench supply: the Pico's `3V3(OUT)` pin can feed the board instead, but first measure
  between the board's `+5V` and `GND` with the multimeter. The forum's most common power-board
  fault is a short on that rail, and the Pico has no current limit to protect it.
- The UI cable is soldered to the mainboard (service manual). To program one board on its own,
  unplug the Picoflex connector at the UI end, gently: two forum users tore off connector pins.

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

## Our power board (photos, 2026-11-17)

Two overview photos of the power board, taken behind the back panel. The photos are kept in
`local/photos/` and are not published. At this resolution no text can be read. What can be
seen, and what still needs a close-up:

| Seen | Probably | Close-up needed |
|---|---|---|
| Mains terminals (blue, green/yellow, brown) and a glass fuse at the bottom left | Mains input and the 1 A fuse the forum mentions | Check that the fuse is intact |
| White sticker next to the fuse | The board label with its 12NC | Yes: the **MAIN 12NC** decides which firmware fits |
| TO-220 part on a heatsink, bottom right | The boiler triac (forum: BTA312) | No |
| Yellow transformer, top left | The switch-mode supply for the 5 V rail | No |
| Small square chip with a white sticker, top right | Possibly the MCU with a software sticker | Yes: chip marking and sticker text |
| 4-pin white connector, top left | Possibly the "white connector" the service manual reserves for the Philips serial programmer | Yes, to tell it apart from the SWD header |
| Flat white cable leaving the top edge | The UI cable, fixed to the mainboard | No |

Still to find: the **5-pin SWD header** near the MCU. The forum's pinout photos
(`pinout.jpg`, `disp-swd-pinout.jpg`) can be seen with a forum account.

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
3. Find the 5-pin SWD header on each board, using the forum pinout photos. Confirm each pin with
   the continuity tester: GND, +5V, and the MCU's SWD data, SWD clock and reset pins.
   - KE02: `SWD_DIO`, `SWD_CLK` and `RESET_b`. Take the pin numbers from the 44-LQFP table in
     the NXP KE02 data sheet ("Signal multiplexing and pin assignments").
   - PSoC 4000S: `SWDIO` = P3.2, `SWDCLK` = P3.3, and `XRES`. This is the usual PSoC 4
     assignment; confirm it in the CY8C4025 data sheet's pin table.

### Step 3: wire up

Mains plug out. Unplug the UI end of the ribbon cable. Connect the bench supply (3.3 V, 50 mA)
to the `+5V` and `GND` test points of the board you are working on. Pico GP2 goes to SWCLK, GP3
to SWDIO, GP1 to RESET (XRES on the UI board) and GND to GND.

### Step 4: dump (read-only, always first)

```sh
cd reflash-ep3243/openocd
./dump.sh main     # power board
./dump.sh ui       # UI board
```

Each run reads the flash three times into `reflash-ep3243/local/dumps/` and compares the
SHA-256 sums. Three identical reads mean the wiring is good. **If OpenOCD reports the KE02 as
secured or the PSoC as `PROTECTED`, stop.** Unlocking erases the chip. Do it only once a
matching replacement image is on disk.

With a J-Link EDU Mini instead, the forum procedure in J-Link Commander (`JLinkExe`) is:
`connect`, choose the device, `S` for SWD, speed `400`, then
`savebin <file> 0x0 0x10000` for the power board (64 KB) or `0x8000` for the UI board (32 KB).

### Step 5: find the versions

```sh
strings -n 6 ../local/dumps/main-*-1.bin | grep -i -E 'v?[0-9]{2}\.[0-9]{2}(\.[0-9]{2})?'
```

Firmware file names on the forum follow the pattern
`main_421941311961_v01.00.02_ep2235.hex` and
`control_panel_421941311861.03_v00.00.01_ep2235.hex`: board 12NC plus version. Compare the
mainboard and UI versions with each other. Whether the version strings are actually stored in
the image is not yet confirmed.

### Step 6: get a matching image

In order of preference:

1. **The forum files** (needs a forum account). Thread 65595 has two firmware attachments:
   - `421941311901.04_v01.01_EP3246.zip`, which a repairer posted as the firmware for the EP3200
     series
   - `control_panel_421941311861.03_v00.00.01_ep2235.zip` for the EP2200 series

   According to the same repairer, `421941311861` revisions `.03` and `.04` are compatible.
   **Match the 12NC from your own board labels to the file names.** If they differ, ask in the
   thread before flashing anything.
2. **A donor board** with the same 12NC (a used spare part, or a board from a broken machine),
   dumped in the same way.
3. **Our own dumps.** Writing them back only helps against corrupted flash, which is rare.

Keep the files in `local/firmware/`. They are Philips' firmware and must never be committed to
this public fork; `.gitignore` blocks `*.hex`, `*.bin` and `*.zip`.

### Step 7: flash

```sh
openocd -f main-ke02.cfg -c "program ../local/firmware/main.hex verify reset exit"
openocd -f ui-psoc4.cfg  -c "program ../local/firmware/ui.hex verify reset exit"
```

For `.bin` files, add the start address: `program <file>.bin 0x0 verify reset exit`. `verify`
reads the flash back and compares it with the file. On the KE02, **never write an image that
changes the flash configuration field at 0x400 to 0x40F.** It holds the security bytes, and a
wrong value can lock the chip for good. An unedited image from a real board is safe.

With J-Link Commander: `loadfile <file.hex>`, then `r`, `g`, `q`. The file path must not
contain spaces (forum).

### Step 8: back together

Plug the ribbon cable back in and close the machine. Then run Steam-Out (step 0) and test mode
level 1 and 2.

## Known failure parts (forum reports, not verified)

- **Power board:** the 1 A fuse, the boiler triac BTA312 and the transistor next to it, the MCU,
  the P-channel MOSFET Q9 (FDN304, which switches the sensor supply on for about 5 s after
  power-up), the logic buffer NL27WZ17 on the RX/TX lines (U2), and 1 kΩ resistors. When the
  fuse blows, mains can reach the 5 V rail and take out everything on it: both MCUs, the water
  level hall sensor, the flowmeter and the NTC.
- **UI board:** the MCU. On the 1200, 2200 and 3200 series the PSoC runs straight from 5 V with
  no regulator.
- The service manual's test tables name a "uP U2 in Main", while a forum post calls U2 the
  NL27WZ17 buffer. The numbering may differ between board revisions.

## Open questions

- The exact SWD header pinout. Answered by the forum photos once the account exists.
- Whether the EP3246 main image (`421941311901.04 v01.01`) fits the EP3243. Our board's 12NC
  label decides it.
- Where the machine parameters live. `flash read_bank` does not read the KE02's 256-byte
  EEPROM. Steam-Out resets the parameters either way.
