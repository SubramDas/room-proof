"""Metric geometry with camera conventions explicit at the boundary."""
import cv2
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares


def backproject(depth,K,rgb_size=None,step=1):
    h,w=depth.shape;intr=K.copy()
    if rgb_size is not None:intr[0]*=w/rgb_size[0];intr[1]*=h/rgb_size[1]
    v,u=np.mgrid[0:h,0:w];p=np.stack(((u-intr[0,2])*depth/intr[0,0],(v-intr[1,2])*depth/intr[1,1],depth),axis=-1)
    return p[::step,::step]


def transform(points,T):return points@T[:3,:3].T+T[:3,3]


def voxel_downsample(p,voxel=.035):
    if len(p)==0:return p
    _,ids=np.unique(np.floor(p/voxel).astype(np.int32),axis=0,return_index=True)
    return p[np.sort(ids)]


def rigid_fit(a,b):
    ac=a.mean(0);bc=b.mean(0);u,_,vt=np.linalg.svd((a-ac).T@(b-bc));r=vt.T@u.T
    if np.linalg.det(r)<0:vt[-1]*=-1;r=vt.T@u.T
    T=np.eye(4);T[:3,:3]=r;T[:3,3]=bc-r@ac
    return T


def icp(source,target,threshold=.15,iterations=15):
    """Trimmed rigid ICP in a shared world frame; reject poorly overlapping fits."""
    T=np.eye(4);tree=cKDTree(target);before=None;fraction=0.;rmse=float('inf')
    if len(source)<30 or len(target)<30:return T,{'accepted':False,'reason':'insufficient_points'}
    for _ in range(iterations):
        moving=transform(source,T);d,j=tree.query(moving,workers=1);good=d<threshold
        fraction=float(good.mean())
        if good.sum()<30:break
        cutoff=np.quantile(d[good],.85);good&=d<=cutoff
        err=float(np.sqrt(np.mean(d[good]**2)))
        if before is None:before=err
        delta=rigid_fit(moving[good],target[j[good]]);T=delta@T;rmse=err
        if np.linalg.norm(delta[:3,3])<.0003 and Rotation.from_matrix(delta[:3,:3]).magnitude()<.0003:break
    angle=float(Rotation.from_matrix(T[:3,:3]).magnitude());shift=float(np.linalg.norm(T[:3,3]))
    accepted=bool(fraction>.30 and rmse<.06 and shift<.20 and angle<.10)
    return T,{'accepted':accepted,'overlap':fraction,'rmse_m':rmse if np.isfinite(rmse) else None,
              'before_rmse_m':before,'translation_m':shift,'rotation_rad':angle}


def correct_pose_graph(clouds,poses,gravity_lock=False):
    """Verified point-cloud factors plus smooth correction priors; never force closure."""
    n=len(poses);edges=[]
    for j in range(1,n):
        if j%2:continue
        i=max(0,j-2);T,info=icp(clouds[j],clouds[i],threshold=.13)
        if info['accepted']:edges.append((i,j,T,'local',info))
    positions=poses[:,:3,3]
    for j in range(12,n,4):
        candidates=np.where(np.linalg.norm(positions[:j-10]-positions[j],axis=1)<.55)[0]
        for i in candidates[::max(1,len(candidates)//3)][:3]:
            look=float(np.dot(poses[i,:3,2],poses[j,:3,2]))
            if look<.75:continue
            T,info=icp(clouds[j],clouds[i],threshold=.18)
            if info['accepted']:edges.append((int(i),j,T,'loop',info));break
    def residual(x):
        x=x.reshape(n,6);rs=[(x[0]*100).ravel(),(x*.7).ravel(),(np.diff(x,axis=0)*2).ravel()]
        for i,j,T,kind,_ in edges:
            target=np.r_[Rotation.from_matrix(T[:3,:3]).as_rotvec(),T[:3,3]]
            if gravity_lock:target[[0,2]]=0.
            rs.append((x[j]-x[i]-target)*(8 if kind=='loop' else 3))
        return np.concatenate(rs)
    if not edges:return poses.copy(),{'method':'verified_ICP_pose_graph','accepted_edges':[],'status':'no_verified_constraints'}
    # Sparse Jacobian structure keeps optimization bounded with hundreds of frames.
    from scipy.sparse import lil_matrix
    m=6+6*n+6*(n-1)+6*len(edges);sp=lil_matrix((m,6*n),dtype=int);row=0
    sp[:6,:6]=1;row=6
    for i in range(n):sp[row:row+6,6*i:6*i+6]=1;row+=6
    for i in range(n-1):sp[row:row+6,6*i:6*i+12]=1;row+=6
    for i,j,*_ in edges:sp[row:row+6,6*i:6*i+6]=1;sp[row:row+6,6*j:6*j+6]=1;row+=6
    result=least_squares(residual,np.zeros(n*6),jac_sparsity=sp.tocsr(),loss='soft_l1',f_scale=.03,max_nfev=25)
    corrected=poses.copy();xs=result.x.reshape(n,6)
    for i,x in enumerate(xs):
        if gravity_lock:x[[0,2]]=0.
        C=np.eye(4);C[:3,:3]=Rotation.from_rotvec(x[:3]).as_matrix();C[:3,3]=x[3:];corrected[i]=C@poses[i]
    return corrected,{'method':'verified_ICP_pose_graph','status':'optimized','small_angle_approximation':True,'gravity_lock':gravity_lock,
        'max_translation_correction_m':float(np.linalg.norm(xs[:,3:],axis=1).max()),
        'accepted_edges':[{'from':i,'to':j,'kind':kind,**info} for i,j,_,kind,info in edges]}


def normal_map(p):
    dy=np.gradient(p,axis=0);dx=np.gradient(p,axis=1);n=np.cross(dx,dy);norm=np.linalg.norm(n,axis=-1)
    return n/np.maximum(norm[...,None],1e-9)


def angle_from_normals(normals):
    a=np.arctan2(normals[:,2],normals[:,0]);weight=np.hypot(normals[:,0],normals[:,2])
    good=(abs(normals[:,1])<.25)&(weight>.8)
    if good.sum()<30:return 0.
    return float(np.angle(np.mean(np.exp(4j*a[good])))/4)


def planar_rotation(angle):
    c,s=np.cos(angle),np.sin(angle)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]])


def plane_modes(values,lo=None,hi=None,bin_size=.025):
    if len(values)<20:return []
    lo=float(np.quantile(values,.005)) if lo is None else lo;hi=float(np.quantile(values,.995)) if hi is None else hi
    if hi-lo<bin_size:return [float(np.median(values))]
    bins=np.arange(lo,hi+bin_size,bin_size);hist,edges=np.histogram(values,bins)
    from scipy.ndimage import gaussian_filter1d
    from scipy.signal import find_peaks
    smooth=gaussian_filter1d(hist.astype(float),1);peaks,_=find_peaks(np.r_[0,smooth,0],distance=5,prominence=max(4,smooth.max()*.035));peaks-=1
    peaks=sorted((p for p in peaks if 0<=p<len(hist)),key=lambda p:-hist[p])[:20]
    result=[]
    for p in peaks:
        center=(edges[p]+edges[p+1])/2;v=values[abs(values-center)<.035]
        if len(v)>15:result.append(float(np.median(v)))
    return sorted(result)


def gravity_alignment(normals):
    """Robust dominant horizontal normals, assuming roughly upright input photos.

    This is an image-derived orientation prior, not an IMU observation. Failure
    on sloped/curved scenes remains possible and must be exposed in RGB QA.
    """
    ns=np.asarray(normals);ns=ns[np.isfinite(ns).all(1)&(abs(ns[:,1])>.70)]
    if len(ns)<100:return np.eye(3)
    ns=ns*np.where(ns[:,1:2]<0,-1.,1.);axis=np.median(ns,axis=0);axis/=np.linalg.norm(axis)
    for _ in range(4):
        use=ns@axis>.96
        if use.sum()<50:break
        axis=np.median(ns[use],axis=0);axis/=np.linalg.norm(axis)
    target=np.array([0.,1.,0.]);cross=np.cross(axis,target);s=np.linalg.norm(cross);c=axis@target
    if s<1e-8:return np.eye(3)
    return Rotation.from_rotvec(cross/s*np.arctan2(s,c)).as_matrix()
