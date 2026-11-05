"""Package only the compiled core Image with the restored v1 installer flow."""
from pathlib import Path
import zipfile,tarfile,shutil
root=Path(__file__).resolve().parents[1]
payload=root/'anykernel';image=payload/'Image'
previous=root/'recovery/Singularity_v2_garnet_KSUN.zip'
if previous.is_file():
 with zipfile.ZipFile(previous) as old:
  assert image.read_bytes()==old.read('Image'),'Core Image unexpectedly changed'
assert image.read_bytes()[56:60]==b'ARM\x64'
assert b'5.10.272-Singularity-v2' in image.read_bytes()
assert not (payload/'payload-modules').exists()
assert not (payload/'tools/garnet_dtb').exists()
script=(payload/'anykernel.sh').read_text()
assert script==(root/'anykernel.sh').read_text()
for forbidden in ['vendor_boot','vendor_dlkm','garnet_dtb','sha256sum','reset_ak','dd if=']:
 assert forbidden not in script,forbidden
assert 'BLOCK=boot' in script and 'SLOT_SELECT=active' in script
meta=payload/'source';meta.mkdir(exist_ok=True)
for p in meta.iterdir():
 if p.is_file():p.unlink()
for name in ['SOURCE.txt','CHANGELOG.txt','VALIDATION.txt','singularity.config']:shutil.copy2(root/name,meta/name)
dest=root/'deliverables';dest.mkdir(exist_ok=True)
zpath=dest/'Singularity_v2_garnet_KSUN.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(payload.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(payload)
  if any(x.startswith('.') for x in rel.parts) or p.name in ['README.md','.gitignore','.gitattributes','placeholder']:continue
  assert p.suffix!='.ko'
  z.write(p,rel.as_posix())
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None
 assert z.read('Image')==image.read_bytes()
 assert z.read('anykernel.sh')==script.encode()
 assert not any(n.endswith('.ko') or n.startswith(('payload-modules/','dtb','vendor_ramdisk/')) for n in z.namelist())
 for n in ['anykernel.sh','META-INF/com/google/android/update-binary','tools/magiskboot','tools/busybox']:
  assert (z.getinfo(n).external_attr>>16)&0o111,n
print('PASS: boot-only ZIP; original v2 compiled Image exact; no vendor payload; CRC and permissions verified',flush=True)
print(zpath,zpath.stat().st_size,flush=True)
src=dest/'Singularity_v2_garnet_KSUN_SOURCE.tar.gz'
def filt(i):
 p=Path(i.name)
 if any(x in ['.git','__pycache__'] for x in p.parts) or i.name.endswith(('.pyc','.orig','.rej')):return None
 if i.name=='anykernel/Image' or i.name.startswith('validation/host_dtb') or any(x.startswith('.Image.') for x in p.parts):return None
 if i.name in ['validation/reference/install-base.json','validation/reference/vendor.symvers']:return None
 return i
with tarfile.open(src,'w:gz',compresslevel=3) as t:
 for name in ['kernel','anykernel','validation','SOURCE.txt','CHANGELOG.txt','VALIDATION.txt','singularity.config','build.sh','anykernel.sh','performance-v2.patch','performance-1.patch','changes.patch']:
  t.add(root/name,arcname=name,filter=filt)
with tarfile.open(src) as t:
 assert t.extractfile('anykernel.sh').read()==script.encode()
 assert t.extractfile('build.sh').read()==(root/'build.sh').read_bytes()
 assert not any(n.endswith('.ko') or 'tools-src/' in n for n in t.getnames())
print('PASS: full corresponding source, boot-only build recipe and installer',flush=True)
print(src,src.stat().st_size,flush=True)
