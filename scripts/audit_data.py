"""Produce a repeatable supplied-data audit without changing raw inputs."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from astra.io import load_scan,photo_groups,sha256,write_json
import numpy as np
root=Path(__file__).resolve().parents[1];scans=[];photos=[];byhash={}
for name in ['kitchen','three_room','Crack_water','single_room','single_scan_floor_only','single_scan_with_ceiling']:
    base=root/name
    if not base.exists():continue
    for odom in sorted(base.rglob('odometry.csv')):
        try:
            scan=load_scan(odom.parent);qa=scan['qa'];qa['path']=str(odom.parent.relative_to(root))
            qa['fx_range_px']=[float(scan['K'][:,0,0].min()),float(scan['K'][:,0,0].max())]
            qa['fy_range_px']=[float(scan['K'][:,1,1].min()),float(scan['K'][:,1,1].max())]
            scans.append(qa)
        except Exception as e:scans.append({'path':str(odom.parent.relative_to(root)),'error':str(e)})
    try:groups=photo_groups(base)
    except ValueError:continue
    for room,files in groups.items():
        photos.append({'dataset':name,'room':room,'image_count':len(files)})
        for f in files:byhash.setdefault(sha256(f),[]).append(str(f.relative_to(root)))
result={'scans':scans,'photos':photos,'duplicate_photos':[v for v in byhash.values() if len(v)>1],
        'decisions':['Use per-frame K; static camera_matrix is only a fallback.','Decode MP4 sample timing and preserve edit-list-hidden frames.',
        'Do not integrate IMU translation; acceleration norms suggest g units.','Two rooms plus corridor retained per user instruction.',
        'Consumer-app comparison unavailable tonight; repeat scans deferred.']}
write_json(root/'reports/data_audit.json',result)
lines=['# Supplied-data audit','','| Dataset | Frames | Seconds | Variable video timing | Acceleration norm | Focal range px |','|---|---:|---:|---|---:|---|']
for s in scans:
    if 'error' in s:lines.append(f"| {s['path']} | ERROR: {s['error']} | | | | |");continue
    lines.append(f"| {s['path']} | {s['frame_count']} | {s['duration_s']:.2f} | {s['variable_video_timing']} | {s['imu_median_acceleration_norm']:.3f} | {s['fx_range_px'][0]:.1f}–{s['fx_range_px'][1]:.1f} |")
lines+=['','## Findings','',f"{len(result['duplicate_photos'])} image hashes occur in multiple folders. These are not independent validation samples.",'','Variable timing, changing intrinsics and likely IMU units are handled by the adapter; no manual edits to sensor files are needed. Keep originals unchanged. A timing mismatch causes a warning rather than an invented frame association.','',*['- '+x for x in result['decisions']]]
(root/'reports/data_audit.md').write_text('\n'.join(lines)+'\n');print(root/'reports/data_audit.md')
