# Decisions

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
| Firmware attachments on saeco-support-forum.de | Rule 3. The attachments return HTTP 403 without a login |
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
