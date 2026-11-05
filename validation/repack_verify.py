"""Repack a disposable boot copy; never access a block device."""
import pathlib,subprocess,tempfile,shutil,sys,hashlib
boot,image,tool=map(lambda p:pathlib.Path(p).resolve(),sys.argv[1:4])
assert boot.is_file() and image.is_file() and tool.is_file()
with tempfile.TemporaryDirectory(prefix='singularity-repack-') as d:
 base=pathlib.Path(d);old=base/'old';new=base/'new';old.mkdir();new.mkdir()
 def run(args,cwd):
  r=subprocess.run([str(tool)]+args,cwd=cwd,capture_output=True,text=True)
  if r.returncode:raise RuntimeError(r.stdout+r.stderr)
  return r.stdout+r.stderr
 run(['unpack','-h',str(boot)],old)
 original_ramdisk=(old/'ramdisk.cpio').read_bytes() if (old/'ramdisk.cpio').exists() else None
 original_header=(old/'header').read_bytes()
 shutil.copyfile(image,old/'kernel')
 packed=base/'boot-new.img'
 run(['repack',str(boot),str(packed)],old)
 assert packed.stat().st_size<=boot.stat().st_size
 log=run(['unpack','-h',str(packed)],new)
 assert (new/'kernel').read_bytes()==image.read_bytes(),'Image changed during repack'
 assert (new/'header').read_bytes()==original_header,'header fields changed'
 new_ramdisk=(new/'ramdisk.cpio').read_bytes() if (new/'ramdisk.cpio').exists() else None
 assert original_ramdisk==new_ramdisk,'ramdisk changed'
 print(log.strip())
 print('PASS: built Image exact; ramdisk exact; header fields retained; fits original boot size')
 print('Image bytes:',image.stat().st_size,'Repacked boot bytes:',packed.stat().st_size)
