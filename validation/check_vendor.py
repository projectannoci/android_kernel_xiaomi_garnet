from pathlib import Path
import json,sys
base=Path(__file__).resolve().parent/'reference'
mods=json.loads((base/'vendor-imports.json').read_text())
provided=set(json.loads((base/'vendor-exports.json').read_text()))
p=Path(sys.argv[1] if len(sys.argv)>1 else 'out/vmlinux.symvers')
core={}
for line in p.read_text().splitlines():
 a=line.split()
 if len(a)>1:core[a[1]]=a[0]
missing={}
for mod,imports in mods.items():
 lost=sorted(set(imports)-provided-set(core))
 if lost:missing[mod]=lost
assert not missing,'Unresolved vendor imports: '+str(missing)
for name in ['cpu_boost_kick','kp_active_mode']:
 expected=mods['msm_drm.ko'][name]
 assert int(core[name],16)==int(expected,16),(name,core[name],expected)
print(f'PASS: {len(mods)} modules; no unresolved names across kernel plus supplied vendor exports')
print('PASS: CPU boost and Kprofiles API CRCs match msm_drm.ko')
print('Static symbol checks do not replace a physical-device boot test.')
