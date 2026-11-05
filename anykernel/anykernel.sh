#!/sbin/sh
properties() { '
kernel.string=Singularity v2
do.devicecheck=1
do.modules=0
do.systemless=0
do.cleanup=1
do.cleanuponabort=1
device.name1=garnet
supported.versions=14-16
supported.patchlevels=
supported.vendorpatchlevels=
'; }
BLOCK=boot
IS_SLOT_DEVICE=auto
SLOT_SELECT=active
RAMDISK_COMPRESSION=auto
NO_MAGISK_CHECK=1
. tools/ak3-core.sh
ui_print 'Singularity v2'
[ -s "$AKHOME/Image" ] || abort 'Kernel payload missing.'
split_boot
strings "$SPLITIMG/kernel" | grep -q '^Linux version 5\.10\.' || abort 'Linux 5.10 is required.'
case "$(sed -n 's/.*HEADER_VER.*\[\([0-9]*\)\].*/\1/p' "$SPLITIMG/infotmp")" in
  3|4) ;;
  *) abort 'Unsupported boot header.' ;;
esac
if [ -f "$SPLITIMG/ramdisk.cpio" ]; then
  unpack_ramdisk
  write_boot
else
  flash_boot
fi
