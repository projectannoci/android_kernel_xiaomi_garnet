#!/sbin/sh
properties() { '
kernel.string=Singularity v1 @ProjectNoci #1
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
PATCH_VBMETA_FLAG=auto
NO_MAGISK_CHECK=1
. tools/ak3-core.sh

ui_print 'Singularity v1 @ProjectNoci #1'
ui_print 'garnet | Linux 5.10 | KSU Next'
split_boot

banner=$(strings "$SPLITIMG/kernel" | grep -m1 '^Linux version 5\.10\.')
[ -n "$banner" ] || abort 'Paket ini memerlukan kernel Linux 5.10 pada garnet.'
case "$(sed -n 's/.*HEADER_VER.*\[\([0-9]*\)\].*/\1/p' "$SPLITIMG/infotmp")" in
  3|4) ;;
  *) abort 'Format boot tidak sesuai.' ;;
esac
[ -s "$AKHOME/Image" ] || abort 'Image kernel tidak tersedia.'

# Retain the existing ramdisk and the active-slot boot header.
if [ -f "$SPLITIMG/ramdisk.cpio" ]; then
  unpack_ramdisk
  write_boot
else
  flash_boot
fi
