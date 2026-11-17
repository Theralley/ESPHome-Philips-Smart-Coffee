# Decisions

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
