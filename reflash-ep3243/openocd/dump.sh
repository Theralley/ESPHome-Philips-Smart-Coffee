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
