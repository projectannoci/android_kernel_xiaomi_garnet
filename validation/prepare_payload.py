"""Stage only the compiled core Image and boot-only installer."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
image=root/'out/arch/arm64/boot/Image'
assert image.read_bytes()[56:60]==b'ARM\x64'
shutil.copy2(image,root/'anykernel/Image')
shutil.copy2(root/'anykernel.sh',root/'anykernel/anykernel.sh')
assert not (root/'anykernel/payload-modules').exists()
print('PASS: boot-only Image payload staged')
