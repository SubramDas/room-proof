from pathlib import Path
import cv2
import numpy as np
from .io import load_scan,write_json,selected_video
from .geometry import backproject,transform,voxel_downsample,normal_map,correct_pose_graph,angle_from_normals,planar_rotation


def reconstruct(path,out,max_frames=160,drift=True,pixel_step=3):
    scan=load_scan(path);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    indices=np.unique(np.linspace(0,len(scan['ids'])-1,min(max_frames,len(scan['ids'])),dtype=int))
    cameras=[];normals=[];raw=[];valid_fractions=[]
    for i in indices:
        d=cv2.imread(str(scan['root']/'depth'/f"{scan['ids'][i]}.png"),cv2.IMREAD_UNCHANGED)
        c=cv2.imread(str(scan['root']/'confidence'/f"{scan['ids'][i]}.png"),cv2.IMREAD_UNCHANGED)
        if d is None or c is None or d.shape!=c.shape:raise ValueError(f'Unreadable paired depth frame {i}')
        depth=d.astype(np.float32)*.001
        pc=backproject(depth,scan['K'][i],(scan['video']['width'],scan['video']['height']),step=1)
        nm=normal_map(pc);valid=(depth>.25)&(depth<6)&(c>=1)
        # Depth jumps invalidate normals and measurements near occlusion boundaries.
        gx=np.abs(np.gradient(depth,axis=1));gy=np.abs(np.gradient(depth,axis=0));valid&=(gx<.10)&(gy<.10)
        sel=valid[::pixel_step,::pixel_step];p=pc[::pixel_step,::pixel_step][sel];n=nm[::pixel_step,::pixel_step][sel]
        cameras.append(p);normals.append(n);raw.append(voxel_downsample(transform(p,scan['poses'][i]),.045));valid_fractions.append(float(valid.mean()))
    before=scan['poses'][indices];after,correction=correct_pose_graph(raw,before) if drift else (before.copy(),{'status':'disabled','accepted_edges':[]})
    pts=[];ns=[];frame_ids=[]
    for k,(p,n,T) in enumerate(zip(cameras,normals,after)):
        pts.append(transform(p,T));ns.append(n@T[:3,:3].T);frame_ids.append(np.full(len(p),k,dtype=np.int32))
    points=np.concatenate(pts);normals=np.concatenate(ns);frame_ids=np.concatenate(frame_ids)
    angle=angle_from_normals(normals);A=planar_rotation(angle)
    points=points@A.T;normals=normals@A.T;pose_transform=np.eye(4);pose_transform[:3,:3]=A
    after=np.einsum('ij,njk->nik',pose_transform,after);before=np.einsum('ij,njk->nik',pose_transform,before)
    raw_points=np.concatenate(raw)@A.T
    np.savez_compressed(out/'geometry.npz',points=points.astype(np.float32),normals=normals.astype(np.float32),
        frame_ids=frame_ids,poses=after,raw_poses=before,indices=indices,K=scan['K'][indices],raw_points=raw_points.astype(np.float32))
    correction['alignment_angle_rad']=angle;write_json(out/'drift.json',correction)
    scan['qa']['selected_frames']=indices.tolist();scan['qa']['valid_depth_fraction_range']=[min(valid_fractions),max(valid_fractions)]
    scan['qa']['point_count']=len(points);write_json(out/'qa.json',scan['qa'])
    print(f'LiDAR: {len(indices)} frames, {len(points):,} points; drift {correction["status"]}',flush=True)
    return {'points':points,'normals':normals,'frame_ids':frame_ids,'poses':after,'raw_poses':before,'indices':indices,
            'K':scan['K'][indices],'scan':scan,'raw_points':raw_points,'qa':scan['qa'],'drift':correction}
