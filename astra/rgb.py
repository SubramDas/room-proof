"""Unposed RGB reconstruction using matching, essential geometry and metric priors."""
from pathlib import Path
import cv2,numpy as np
from .io import photo_groups,selected_video,mp4_info,write_json
from .vision import MetricDepth,DepthPro,focal_guess
from .geometry import backproject,normal_map,transform,angle_from_normals,planar_rotation,gravity_alignment


def prepare_views(path,tier,out,max_frames=40,rotation=0):
    out=Path(out);views=[]
    if tier=='photos':
        groups=photo_groups(path)
        for room,files in groups.items():
            for p in files:views.append({'source':str(p),'image':str(p),'room_hint':room})
    else:
        meta=mp4_info(path);indices=np.unique(np.linspace(0,meta['samples']-1,min(max_frames,meta['samples']),dtype=int))
        views=selected_video(path,indices,out/'keyframes');
        for v in views:v['source']=f'{path}#frame={v["frame_index"]}';v['room_hint']=None
    for i,v in enumerate(views):
        image=cv2.imread(v['image'])
        if image is None:raise ValueError(f'Unreadable image {v["image"]}')
        if rotation:image=cv2.rotate(image,{90:cv2.ROTATE_90_CLOCKWISE,180:cv2.ROTATE_180,270:cv2.ROTATE_90_COUNTERCLOCKWISE}[rotation])
        scale=min(1,800/max(image.shape[:2]));image=cv2.resize(image,(round(image.shape[1]*scale),round(image.shape[0]*scale)))
        v['bgr']=image;v['id']=i;f,method=focal_guess(image);h,w=image.shape[:2];v['K']=np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])
        v['intrinsics_method']=method
    return views


def match_pair(a,b):
    matches=cv2.BFMatcher().knnMatch(a['desc'],b['desc'],k=2)
    good=[m for pair in matches if len(pair)==2 for m,n in [pair] if m.distance<.72*n.distance]
    if len(good)<15:return None
    pa=np.float32([a['keypoints'][m.queryIdx].pt for m in good]);pb=np.float32([b['keypoints'][m.trainIdx].pt for m in good])
    # Depth-assisted PnP also handles rotation-dominated views for which
    # essential-matrix triangulation cannot establish stable translation.
    px=np.rint(pa).astype(int)
    za=a['depth'][np.clip(px[:,1],0,a['depth'].shape[0]-1),np.clip(px[:,0],0,a['depth'].shape[1]-1)]
    xyz=(np.c_[pa,np.ones(len(pa))]@np.linalg.inv(a['K']).T)*za[:,None]
    valid=np.isfinite(xyz).all(1)&(za>.25)&(za<15)
    if valid.sum()>=20:
        ok,rv,tv,inliers=cv2.solvePnPRansac(xyz[valid].astype(np.float32),pb[valid],b['K'],None,
            iterationsCount=300,reprojectionError=2.5,confidence=.999,flags=cv2.SOLVEPNP_EPNP)
        if ok and inliers is not None and len(inliers)>=20 and len(inliers)/valid.sum()>.4:
            use=np.where(valid)[0][inliers.ravel()]
            rv,tv=cv2.solvePnPRefineLM(xyz[use],pb[use],b['K'],None,rv,tv)
            R=cv2.Rodrigues(rv)[0];T=np.eye(4);T[:3,:3]=R;T[:3,3]=tv.ravel()
            if np.linalg.norm(tv)<8:
                proj,_=cv2.projectPoints(xyz[use],rv,tv,b['K'],None)
                error=float(np.median(np.linalg.norm(proj[:,0]-pb[use],axis=1)))
                return {'from':a['id'],'to':b['id'],'T_to_from':T,'inliers':len(use),'matches':len(good),
                    'scale':1.,'scale_iqr':error/2.5,'pose_source':'depth_assisted_PnP','reprojection_median_px':error,
                    'points_a':pa[use],'points_b':pb[use]}
    na=cv2.undistortPoints(pa[:,None,:],a['K'],None)[:,0];nb=cv2.undistortPoints(pb[:,None,:],b['K'],None)[:,0]
    E,mask=cv2.findEssentialMat(na,nb,np.eye(3),method=cv2.RANSAC,prob=.999,threshold=.0025)
    if E is None or E.shape!=(3,3):return None
    count,R,t,mask=cv2.recoverPose(E,na,nb,np.eye(3),mask=mask)
    use=mask.ravel()>0
    if count<12 or count/len(good)<.2:return None
    xyz=cv2.triangulatePoints(np.c_[np.eye(3),np.zeros(3)],np.c_[R,t],na[use].T,nb[use].T);xyz=(xyz[:3]/xyz[3]).T
    px=np.rint(pa[use]).astype(int);depth=a['depth'][np.clip(px[:,1],0,a['depth'].shape[0]-1),np.clip(px[:,0],0,a['depth'].shape[1]-1)]
    valid=(xyz[:,2]>.1)&(xyz[:,2]<150)&(depth>.2)&(depth<15)
    if valid.sum()<10:return None
    scales=depth[valid]/xyz[valid,2];scale=float(np.median(scales));spread=float(np.quantile(scales,.75)-np.quantile(scales,.25))
    if not .005<scale<20:return None
    T=np.eye(4);T[:3,:3]=R;T[:3,3]=t.ravel()*scale
    return {'from':a['id'],'to':b['id'],'T_to_from':T,'inliers':int(count),'matches':len(good),'scale':scale,'scale_iqr':spread,'points_a':pa[use],'points_b':pb[use]}


def reconstruct_rgb(path,tier,out,models=None,device='cpu',max_frames=40,rotation=0,depth_model='small'):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);views=prepare_views(path,tier,out,max_frames,rotation)
    model=(DepthPro(models,device,quantized=depth_model=='depth-pro-int8') if depth_model.startswith('depth-pro') else MetricDepth(models,device));sift=cv2.SIFT_create(nfeatures=1800)
    for v in views:
        if depth_model.startswith('depth-pro'):
            v['depth'],f=model.predict_with_focal(v['bgr'],out/'depth_cache');v['K'][0,0]=f;v['K'][1,1]=f;v['intrinsics_method']='DepthPro_learned_focal'
        else:v['depth']=model.predict(v['bgr'],out/'depth_cache')
        v['keypoints'],v['desc']=sift.detectAndCompute(cv2.cvtColor(v['bgr'],cv2.COLOR_BGR2GRAY),None)
        print(f'{tier}: depth and features {v["id"]+1}/{len(views)}',flush=True)
    edges=[]
    for i,a in enumerate(views):
        if a['desc'] is None:continue
        for j in range(i+1,len(views)):
            b=views[j]
            if b['desc'] is None:continue
            if tier=='video' and j-i>3 and (j-i<10 or j%8 or i%8):continue
            edge=match_pair(a,b)
            if edge:edges.append(edge)
    # Maximum-support spanning forest. Disconnected components remain explicit.
    poses=[None]*len(views);component=[None]*len(views);cid=0;used=[]
    while any(p is None for p in poses):
        start=next(i for i,p in enumerate(poses) if p is None);poses[start]=np.diag([1.,-1.,-1.,1.]);component[start]=cid
        while True:
            possible=[e for e in edges if (poses[e['from']] is None)!=(poses[e['to']] is None)]
            if not possible:break
            e=max(possible,key=lambda e:e['inliers']/(1+e['scale_iqr']/max(e['scale'],1e-6)));i,j=e['from'],e['to']
            if poses[i] is not None:poses[j]=poses[i]@np.linalg.inv(e['T_to_from']);component[j]=component[i]
            else:poses[i]=poses[j]@e['T_to_from'];component[i]=component[j]
            used.append(e)
        cid+=1
    # Refine the connected pose graph with all verified relative-view factors.
    # Weak scale factors remain learned priors; this does not create metric truth.
    from scipy.optimize import least_squares
    from scipy.spatial.transform import Rotation
    refined=[]
    for c in range(cid):
        ids=[i for i,cc in enumerate(component) if cc==c];local={v:k for k,v in enumerate(ids)}
        ce=[e for e in edges if component[e['from']]==c and component[e['to']]==c]
        if len(ids)<3 or len(ce)<len(ids):continue
        initial=np.array([np.r_[Rotation.from_matrix(poses[i][:3,:3]).as_rotvec(),poses[i][:3,3]] for i in ids])
        def unpack(x):
            x=x.reshape(-1,6);Ts=np.tile(np.eye(4),(len(ids),1,1));Ts[:,:3,:3]=Rotation.from_rotvec(x[:,:3]).as_matrix();Ts[:,:3,3]=x[:,3:];return Ts
        def residual(x):
            Ts=unpack(x);rr=[(x.reshape(-1,6)[0]-initial[0])*30]
            for e in ce:
                a,b=local[e['from']],local[e['to']];pred=np.linalg.inv(Ts[b])@Ts[a];target=e['T_to_from']
                weight=min(2.,np.sqrt(e['inliers']/30)) / (1+e['scale_iqr']/max(e['scale'],1e-6))
                rr.append(np.r_[Rotation.from_matrix(pred[:3,:3]@target[:3,:3].T).as_rotvec(),(pred[:3,3]-target[:3,3])*.3]*weight)
            return np.concatenate(rr)
        fit=least_squares(residual,initial.ravel(),loss='soft_l1',f_scale=.05,max_nfev=15)
        for i,T in zip(ids,unpack(fit.x)):poses[i]=T
        refined.append({'component':c,'edges':len(ce),'cost':float(fit.cost)})
    components=[]
    for c in range(cid):
        ids=[i for i,cc in enumerate(component) if cc==c];points=[];normals=[];fids=[]
        for k,i in enumerate(ids):
            v=views[i];pc=backproject(v['depth'],v['K']);nm=normal_map(pc);valid=(v['depth']>.25)&(v['depth']<12)
            sel=valid[::5,::5];p=pc[::5,::5][sel];n=nm[::5,::5][sel];points.append(transform(p,poses[i]));normals.append(n@poses[i][:3,:3].T);fids.append(np.full(len(p),k))
        p=np.concatenate(points);n=np.concatenate(normals);G=gravity_alignment(n);A=planar_rotation(angle_from_normals(n@G.T))@G;T=np.eye(4);T[:3,:3]=A
        ps=np.array([T@poses[i] for i in ids]);p=p@A.T;n=n@A.T
        components.append({'points':p,'normals':n,'frame_ids':np.concatenate(fids).astype(int),'poses':ps,'view_ids':ids})
        for i,pose in zip(ids,ps):views[i]['pose']=pose;views[i]['component']=c
    summary={'model':model.description,'view_count':len(views),'connected_components':cid,'registered_edges':len(edges),
        'pose_method':'depth_PnP_or_essential_with_metric_prior_and_pose_graph','pose_graph_refinements':refined,'scale_status':'learned_prior_not_survey_calibrated',
        'views':[{'id':v['id'],'source':v['source'],'room_hint':v['room_hint'],'component':v['component'],'K':v['K'],'pose':v['pose'],'intrinsics_method':v['intrinsics_method']} for v in views],
        'edges':[{k:v for k,v in e.items() if k not in ['points_a','points_b']} for e in edges],
        'warnings':['Metric depth and focal priors may have large systematic scale bias.','Disconnected components have no observed relative placement.']}
    write_json(out/'rgb_reconstruction.json',summary)
    return components,views,summary
