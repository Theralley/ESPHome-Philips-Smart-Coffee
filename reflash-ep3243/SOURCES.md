# Sources

Checked on 2026-11-17. Copies of the documents are kept in `local/sources/`, which is
gitignored: they are Philips' and other people's material and are not republished here. The
SHA-256 sums identify the exact copies that were read.

## Philips documents

| Document | What it establishes | Local copy (SHA-256) |
|---|---|---|
| [Philips EP Series service manual, EP3243/50, v1.5 (2023-04-13)](https://www.atarserviss.lv/image/files/Philips/Philips%203200/EP3243-50-1.pdf) | Disassembly (pp. 22–29); test mode `B5-B2-B4-B3` (p. 30); Steam-Out `B4-B2-B5-B3` resets the parameters (p. 40) and warns against a serial connection on the mainboard's white connector; EPSC with "KIT PROGRAMMER SERKIT SSC2" `996530009845` and cable `421946047151` "WIRING SERPROG OMN PROGRAMMER ASSY." (p. 45); "The board is working at 230V" | `ce3888ebc84ba07025676867725eaa712bd57f84dcf7ac49e958bd6c9902b8e3` |
| [EPSC Quick Start Guide](https://www.epsc.versuni.com/ServiceCenterPortal/DownloadData/EPSC-QuickStart.pdf) | Windows Vista to 10 plus .NET 4.0; registration with company name and e-mail, which returns a Service Center Key; a diagnostics read is mandatory before a firmware upgrade; separate MAIN and UI versions on 230 V EP models (SDA_115422); the key can be locked out for "abuse" | `db8c53af2a68af2e2cec02a1d4d745d11d5cf20570c8497d9c98ff80df97aefc` |

## Community sources

| Source | What it establishes |
|---|---|
| [saeco-support-forum.de, thread 65595 "LatteGo 2231/40 neue Platine programmieren?"](https://saeco-support-forum.de/threads/lattego-2231-40-neue-platine-programmieren.65595/), 3 pages, 2025-03 to 2026-10 | The MCUs are MKE02Z64VLD4 (power board) and CY8C4025 (UI board), programmed over SWD. The power boards of the EP1200 to EP5400 are identical apart from the firmware. Firmware has not been read-protected on any board the repairer saw. Programming works with a J-Link EDU Mini and J-Link Commander with the board on 3.3 V, and the thread includes the Commander procedure. A firmware mismatch can pause heating for 30 s, and the thread lists the parts that typically fail. The firmware and pinout attachments return HTTP 403 without a login. Local text extract SHA-256 `3b6d58ef08fcd60d3f75949b63e1ecb8a65d884dae36cbf3670e1016d527672f` |
| [hackcorrelation: Philips 3200 coffee machine, part 1](https://hackcorrelation.blogspot.com/2021/05/philips-3200-coffee-machine-part-1.html) | The UI board is "Omnia UI Basic" with a CY8C4025AZI-S413, and it talks to the mainboard over UART at 115200 baud |
| [TillFleisch/ESPHome-Philips-Smart-Coffee](https://github.com/TillFleisch/ESPHome-Philips-Smart-Coffee) (upstream of this fork) | Supports the EP3243 from v3.0.0. Pinout of the 8-pin ribbon cable. The ESP sits between the boards as a man-in-the-middle and does not change the Philips firmware |
| [Upstream issue #19](https://github.com/TillFleisch/ESPHome-Philips-Smart-Coffee/issues/19) and [#90](https://github.com/TillFleisch/ESPHome-Philips-Smart-Coffee/issues/90) | The display can stay dark while the mainboard runs. Some displays send unknown commands, possibly from different firmware |

## Chip and tool references

| Source | What it establishes |
|---|---|
| NXP KE02 sub-family data sheet ([mirror used](https://datasheet.chipsmall.com/MKE02Z32VFM4/587205.pdf); nxp.com returned 404) | MKE02Z64VLD4 = 44-LQFP, 64 KB flash, up to 256 B EEPROM, SWD only. Local copy SHA-256 `1e796e908fa6ba2181aa0aa72d7b4c7d868986bcc08be2ab47813f1ebeb744f2`. The pin table is not in the extracted text; check it in the PDF |
| [NXP KE02 data sheet MKE02P64M40SF0](https://www.nxp.com/docs/en/data-sheet/MKE02P64M40SF0.pdf) (rev. 7, via web search; the direct download returned 404 here) and [NXP community: SWD pins used as GPIO on MKE02Z64](https://community.nxp.com/t5/Kinetis-Microcontrollers/Problem-programming-and-debugging-after-using-SWD-and-CLK-ports/td-p/439389) | 44-LQFP: pin 42 = PTC4 = SWD_CLK, pin 44 = PTA4 = SWD_DIO. If firmware repurposes them, connect under reset. The RESET_b pin number has not been checked yet |
| Our own photos of the power board, 2026-11-17 (`local/photos/`, not published: GPS in EXIF) | PCB `1.9.30.330.00 V11`; labels `421945023121/02` (crossed out) and `421945017971 V.01.05.02`; MCU sticker `V.01.01.05 CD2734BF`; TP11 +5V, TP14 GND, TP13 U_TX, TP12 U_RX; JP19 2×5 pads; white 5-pin header; JP9 UI socket |
| [KE02 Sub-Family Reference Manual, rev. 3 (mirror)](https://www.zlgmcu.com/data/upload/file/Utilitymcu/MKE02.pdf) | Table 4-1: EEPROM at `0x1000_0000–0x1000_00FF`. Table 18-6: flash configuration field (`0x40C` EEPROM protection, `0x40D` flash protection, `0x40E` security byte, `0x40F` nonvolatile). Section 8.2 and FSEC: SEC=`10` means unsecured; when secured, only mass erase is possible over the debug port |
| [OpenOCD `tcl/target/ke0x.cfg`](https://github.com/openocd-org/openocd/blob/master/tcl/target/ke0x.cfg) and [`src/flash/nor/kinetis_ke.c`](https://github.com/openocd-org/openocd/blob/master/src/flash/nor/kinetis_ke.c) | KE0x support over SWD, including the KE02 sub-family, plus `kinetis_ke mdm check_security` and `mass_erase` |
| [OpenOCD `tcl/target/psoc4.cfg`](https://github.com/openocd-org/openocd/blob/master/tcl/target/psoc4.cfg) and [`src/flash/nor/psoc4.c`](https://github.com/openocd-org/openocd/blob/master/src/flash/nor/psoc4.c) | PSoC 4 flash driver; reports chip protection as VIRGIN, open, PROTECTED or KILL |
| [raspberrypi/debugprobe](https://github.com/raspberrypi/debugprobe) | Runs on a Pico or Pico 2. `board_pico_config.h`: SWCLK on GP2, SWDIO on GP3, RESET on GP1, LED on GP25. Release v2.3.1 includes `debugprobe_on_pico.uf2` |
| debugprobe issues [#41](https://github.com/raspberrypi/debugprobe/issues/41) and [#160](https://github.com/raspberrypi/debugprobe/issues/160) | Pico W: no official build and no LED support. A maintainer in #41 suggests `-DPICO_BOARD=pico_w`; #160 says it is untested |
| [SEGGER J-Link downloads](https://www.segger.com/downloads/jlink/) | J-Link Software and Documentation Pack for macOS (Apple Silicon, Intel and universal); download after accepting the terms of use |
| Homebrew | `open-ocd` 0.12.0, `srecord` 1.65.0 |

## Not verified

- The SWD header pinout on these boards. The forum photos `pinout.jpg` and `disp-swd-pinout.jpg` need a login.
- The contents of the forum firmware zips (`421941311901.04_v01.01_EP3246.zip` and `control_panel_421941311861.03_v00.00.01_ep2235.zip`). Not downloaded yet.
- Whether `debugprobe_on_pico.uf2` runs on our Pico W.
- The exact KE02 and PSoC pin numbers for SWD on these packages.
- Whether the firmware version string is stored inside the image.
- A price or a seller for the Serkit SSC2 (not needed under the ground rules).
