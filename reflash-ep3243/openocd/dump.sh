#!/bin/sh
# Read-only. Reads one MCU's flash three times and checks that the reads match.
# Usage: ./dump.sh main|ui
# Writes to ../local/dumps/ (gitignored). Not yet run on real hardware.
set -eu

cd "$(dirname "$0")"

board="${1:-}"
case "$board" in
  main) cfg=main-ke02.cfg; check='kinetis_ke mdm check_security' ;;
  ui)   cfg=ui-psoc4.cfg;  check='flash info 0' ;;
  *)    echo "usage: $0 main|ui" >&2; exit 2 ;;
esac

if ! system_profiler SPUSBDataType 2>/dev/null | grep -qi cmsis-dap; then
  echo "No CMSIS-DAP probe on USB. Is the Pico plugged in and running debugprobe" >&2
  echo "(not blueTag's menu)? See 'Turning the Pico W into a probe' in the README." >&2
  exit 1
fi

out=../local/dumps
mkdir -p "$out"
stamp=$(date +%Y%m%d-%H%M%S)

for i in 1 2 3; do
  openocd -f "$cfg" \
    -c init \
    -c "$check" \
    -c "reset halt" \
    -c "flash read_bank 0 $out/$board-$stamp-$i.bin" \
    -c shutdown
done

shasum -a 256 "$out/$board-$stamp"-*.bin
unique=$(shasum -a 256 "$out/$board-$stamp"-*.bin | awk '{print $1}' | sort -u | wc -l | tr -d ' ')
if [ "$unique" = 1 ]; then
  echo "OK: three identical reads of the $board board."
else
  echo "MISMATCH: the reads differ. Check the wiring, the supply and the adapter speed." >&2
  exit 1
fi

# KE02 only: also save the 256-byte EEPROM (machine parameters), mapped at
# 0x10000000 (KE02 reference manual, table 4-1). For reference only: OpenOCD
# cannot write it back, and Steam-Out resets the parameters anyway.
if [ "$board" = main ]; then
  if openocd -f "$cfg" -c init -c "reset halt" \
       -c "dump_image $out/main-eeprom-$stamp.bin 0x10000000 256" -c shutdown; then
    shasum -a 256 "$out/main-eeprom-$stamp.bin"
  else
    echo "WARNING: EEPROM read failed. The flash dumps above are still valid." >&2
  fi
fi
