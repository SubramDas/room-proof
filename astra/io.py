"""Input adapters: immutable sources and explicit modality boundaries."""
from pathlib import Path
import csv, hashlib, json, struct
import cv2
import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation

IMAGE_SUFFIXES={'.jpg','.jpeg','.png','.heic','.webp'}


def write_json(path, data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,indent=2,allow_nan=False,default=lambda x:x.tolist() if hasattr(x,'tolist') else str(x))+'\n')


def sha256(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def csv_rows(path):
    with Path(path).open() as f:
        return [{k.strip():v.strip() for k,v in r.items()} for r in csv.DictReader(f)]


def scan_root(path):
    p=Path(path)
    if (p/'odometry.csv').exists():return p
    matches=sorted(p.glob('**/odometry.csv'))
    if len(matches)!=1:raise ValueError(f'Expected one scan under {p}; found {len(matches)}. Pass a specific scan directory.')
    return matches[0].parent


def atoms(f,start,end):
    pos=start
    while pos+8<=end:
        f.seek(pos); size,kind=struct.unpack('>I4s',f.read(8));header=8
        if size==1:size=struct.unpack('>Q',f.read(8))[0];header=16
        if size==0:size=end-pos
        if size<header or pos+size>end:raise ValueError('Invalid MP4 atom length')
        yield kind,pos+header,pos+size
        pos+=size


def mp4_info(path):
    """Read sample timing without assuming a constant frame rate; no pixel decode."""
    path=Path(path); tracks=[]
    with path.open('rb') as f:
        def children(a,b):return list(atoms(f,a,b))
        for kind,a,b in children(0,path.stat().st_size):
            if kind!=b'moov':continue
            for kind,a,b in children(a,b):
                if kind!=b'trak':continue
                t={}
                def walk(a,b):
                    for kind,c,d in children(a,b):
                        if kind in [b'mdia',b'minf',b'stbl',b'edts']:walk(c,d)
                        else:
                            f.seek(c); v=f.read(d-c)
                            if kind==b'hdlr':t['handler']=v[8:12].decode()
                            elif kind==b'mdhd':
                                off=20 if v[0] else 12;t['timescale']=struct.unpack_from('>I',v,off)[0]
                                dur=struct.unpack_from('>Q' if v[0] else '>I',v,off+4)[0];t['duration_s']=dur/t['timescale']
                            elif kind==b'tkhd':t['width'],t['height']=[x/65536 for x in struct.unpack_from('>II',v,len(v)-8)]
                            elif kind==b'stsz':t['samples']=struct.unpack_from('>I',v,8)[0]
                            elif kind in [b'stts',b'ctts']:
                                n=struct.unpack_from('>I',v,4)[0];fmt='>Ii' if kind==b'ctts' and v[0]==1 else '>II'
                                t[kind.decode()]=[struct.unpack_from(fmt,v,8+i*8) for i in range(n)]
                walk(a,b)
                if t.get('handler')=='vide':tracks.append(t)
    if not tracks:raise ValueError('No video track')
    t=tracks[0];durations=np.repeat([v for _,v in t['stts']],[n for n,_ in t['stts']])
    dts=np.r_[0,np.cumsum(durations[:-1])]
    offsets=np.repeat([v for _,v in t.get('ctts',[])],[n for n,_ in t.get('ctts',[])])
    pts=np.sort(dts+(offsets if len(offsets)==len(dts) else 0)).astype(float)/t['timescale']
    t['relative_pts_s']=(pts-pts[0]).tolist();t['variable_frame_timing']=len(set(durations))>1
    t.pop('stts',None);t.pop('ctts',None)
    return t


def load_scan(path):
    root=scan_root(path); rows=csv_rows(root/'odometry.csv')
    if not rows:raise ValueError('Empty pose CSV')
    required=['timestamp','frame','x','y','z','qx','qy','qz','qw']
    if any(k not in rows[0] for k in required):raise ValueError('Unsupported pose columns')
    ids=[r['frame'] for r in rows];ts=np.array([float(r['timestamp']) for r in rows])
    if len(set(ids))!=len(ids) or (np.diff(ts)<=0).any():raise ValueError('Duplicate frame IDs or nonmonotonic timestamps')
    for folder in ['depth','confidence']:
        available={p.stem for p in (root/folder).glob('*.png')}
        if set(ids)!=available:raise ValueError(f'{folder} IDs do not match poses')
    q=np.array([[float(r[k]) for k in ['qx','qy','qz','qw']] for r in rows])
    if not np.isfinite(q).all() or np.max(abs(np.linalg.norm(q,axis=1)-1))>.01:raise ValueError('Invalid pose quaternion')
    poses=np.tile(np.eye(4),(len(rows),1,1));poses[:,:3,:3]=Rotation.from_quat(q).as_matrix()
    poses[:,:3,3]=[[float(r[k]) for k in ['x','y','z']] for r in rows]
    K=np.tile(np.eye(3),(len(rows),1,1))
    if all(k in rows[0] for k in ['fx','fy','cx','cy']):
        for i,r in enumerate(rows):K[i,0,0],K[i,1,1],K[i,0,2],K[i,1,2]=[float(r[k]) for k in ['fx','fy','cx','cy']]
    else:K[:]=np.loadtxt(root/'camera_matrix.csv',delimiter=',')
    if not np.isfinite(K).all() or (K[:,:2,:2].diagonal(axis1=1,axis2=2)<=0).any():raise ValueError('Invalid intrinsics')
    meta=mp4_info(root/'rgb.mp4')
    if meta['samples']!=len(rows):raise ValueError('RGB/pose counts disagree; pairing needs explicit recovery')
    residual=np.array(meta['relative_pts_s'])-(ts-ts[0])
    imu=csv_rows(root/'imu.csv'); acc=np.array([[float(r[k]) for k in ['a_x','a_y','a_z']] for r in imu])
    norm=float(np.median(np.linalg.norm(acc,axis=1)))
    qa={'frame_count':len(rows),'duration_s':float(ts[-1]-ts[0]),'rgb_size':[meta['width'],meta['height']],
        'depth_units':'mm','pose_units':'m','pose_convention':'camera_to_world_xyzw_OpenCV_camera_y_world_up',
        'intrinsics_source':'per_frame' if 'fx' in rows[0] else 'static_fallback',
        'variable_video_timing':meta['variable_frame_timing'],'rgb_pose_timing_max_residual_s':float(abs(residual).max()),
        'imu_median_acceleration_norm':norm,'imu_unit_assessment':'likely_g' if .8<norm<1.2 else 'unconfirmed',
        'imu_translation_integration':False,'warnings':[]}
    if abs(residual).max()>.075:qa['warnings'].append('RGB/depth timing mismatch: semantic projection requires extra verification')
    return {'root':root,'ids':ids,'timestamps':ts,'poses':poses,'K':K,'video':meta,'qa':qa}


def photo_groups(path):
    p=Path(path)
    if p.is_file():raise ValueError('Photos require a room folder or per-room folders')
    root_files=sorted(x for x in p.iterdir() if x.is_file() and x.suffix.lower() in IMAGE_SUFFIXES)
    if root_files:return {p.name:root_files}
    groups={}
    for child in sorted(p.iterdir()):
        if not child.is_dir() or child.name in ['lidar','depth','confidence']:continue
        photos=sorted(x for x in child.iterdir() if x.is_file() and x.suffix.lower() in IMAGE_SUFFIXES)
        if photos:groups[child.name]=photos
    if not groups:raise ValueError('No photos found')
    for name,files in groups.items():
        if not 2<=len(files)<=8:raise ValueError(f'{name}: photo contract is 2–8 images, found {len(files)}')
    return groups


def selected_video(path, indices, output, max_width=960):
    indices=set(map(int,indices));output=Path(output);output.mkdir(parents=True,exist_ok=True)
    cap=cv2.VideoCapture(str(path)); selected=[];i=0
    if not cap.isOpened():raise ValueError(f'Cannot decode video {path}')
    try:
        while i<=max(indices,default=-1):
            ok=cap.grab()
            if not ok:break
            if i in indices:
                ok,img=cap.retrieve()
                if not ok:raise ValueError(f'Video decode failed at frame {i}')
                if img.shape[1]>max_width:img=cv2.resize(img,(max_width,round(img.shape[0]*max_width/img.shape[1])))
                dest=output/f'{i:06d}.jpg';cv2.imwrite(str(dest),img,[cv2.IMWRITE_JPEG_QUALITY,92])
                selected.append({'frame_index':i,'image':str(dest),'decoder_pts_s':cap.get(cv2.CAP_PROP_POS_MSEC)/1000})
            i+=1
    finally:cap.release()
    if len(selected)!=len(indices):raise ValueError(f'Expected {len(indices)} selected frames, decoded {len(selected)}')
    return selected


def input_manifest(files,base):
    base=Path(base).resolve()
    return [{'path':str(Path(p).resolve().relative_to(base)),'sha256':sha256(p),'bytes':Path(p).stat().st_size} for p in sorted(files)]
