"""Run the real AnyKernel entry with host-only partition operations."""
import pathlib,shutil,subprocess,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class InstallerTest(unittest.TestCase):
 def run_case(self,banner,header=4,ramdisk=True,payload=True):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp);(p/'tools').mkdir();(p/'split_img').mkdir()
   shutil.copy2(ROOT/'anykernel/anykernel.sh',p/'anykernel.sh')
   if payload:(p/'Image').write_bytes(b'fixture image')
   (p/'split_img/kernel').write_text(banner)
   (p/'split_img/infotmp').write_text(f'HEADER_VER [{header}]\n')
   if ramdisk:(p/'split_img/ramdisk.cpio').write_bytes(b'retain ramdisk')
   (p/'tools/ak3-core.sh').write_text('''
AKHOME=$PWD
SPLITIMG=$PWD/split_img
ui_print() { :; }
abort() { echo "$*"; exit 1; }
split_boot() { :; }
unpack_ramdisk() { echo unpack >> intent; }
write_boot() { echo write >> intent; }
flash_boot() { echo flash >> intent; }
''')
   run=subprocess.run(['sh','anykernel.sh'],cwd=p,capture_output=True,text=True)
   intent=(p/'intent').read_text() if (p/'intent').exists() else ''
   return run.returncode,intent,run.stdout
 def test_booted_garnet_ramdisk_is_retained(self):
  rc,ops,_=self.run_case('Linux version 5.10.272-Singularity-v1-ProjectNoci')
  self.assertEqual((rc,ops),(0,'unpack\nwrite\n'))
 def test_boot_without_ramdisk(self):
  rc,ops,_=self.run_case('Linux version 5.10.269-Kitsune-SpiritFox',ramdisk=False)
  self.assertEqual((rc,ops),(0,'flash\n'))
 def test_wrong_kernel_aborts_before_write(self):
  rc,ops,_=self.run_case('Linux version 6.1.99')
  self.assertNotEqual(rc,0);self.assertEqual(ops,'')
 def test_wrong_header_aborts_before_write(self):
  rc,ops,_=self.run_case('Linux version 5.10.272',header=2)
  self.assertNotEqual(rc,0);self.assertEqual(ops,'')
 def test_missing_payload_aborts_before_write(self):
  rc,ops,_=self.run_case('Linux version 5.10.272',payload=False)
  self.assertNotEqual(rc,0);self.assertEqual(ops,'')
if __name__=='__main__':unittest.main()
