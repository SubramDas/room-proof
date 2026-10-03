"""LiDAR opening candidates require both a wall gap and rays passing through it."""
import numpy as np
from scipy.ndimage import gaussian_filter1d,label
from .layout import measure


def geometric_openings(geo,surfaces):
    p=geo['points'];origins=geo['poses'][geo['frame_ids'],:3,3];rays=p-origins;items=[]
    for s in surfaces:
        if s['kind']!='wall':continue
        a=np.array(s['start']);b=np.array(s['end']);edge=b-a;L=np.linalg.norm(edge)
        if L<.45:continue
        e=edge/L;n=np.array([-e[1],e[0]]);q=p[:,[0,2]]-a
        u=q@e;y=p[:,1]-s['floor_y'];distance=q@n
        bins=np.linspace(0,L,max(3,int(np.ceil(L/.015)))+1);centers=(bins[:-1]+bins[1:])/2
        onwall=(abs(distance)<.04)&(y>.4)&(y<1.85)
        wall=np.histogram(u[onwall],bins)[0].astype(float)
        den=rays[:,[0,2]]@n;num=(a-origins[:,[0,2]])@n
        t=np.divide(num,den,out=np.full(len(p),-1.),where=abs(den)>.02)
        passmask=(t>.02)&(t<.98)&((1-t)*np.linalg.norm(rays,axis=1)>.18)&(abs(num)>.15)
        ids=np.where(passmask)[0]
        if len(ids)<30:continue
        cross=origins[ids]+t[ids,None]*rays[ids];cu=(cross[:,[0,2]]-a)@e;cy=cross[:,1]-s['floor_y']
        counts=np.array([np.histogram(cu[(cy>lo)&(cy<hi)],bins)[0] for lo,hi in [(.35,.85),(.85,1.35),(1.35,1.85)]])
        through=gaussian_filter1d(counts.astype(float),1,axis=1)
        smoothed=gaussian_filter1d(wall,1);positive=smoothed[smoothed>3]
        if not len(positive):continue
        void=(np.sum(through>2,axis=0)>=2)&(smoothed<max(5.,np.median(positive)*.13))
        labs,numlab=label(void)
        for k in range(1,numlab+1):
            use=np.where(labs==k)[0];lo=bins[use[0]];hi=bins[use[-1]+1];width=hi-lo
            if not .4<width<2.:continue
            evidence=ids[(cu>=lo)&(cu<=hi)&(cy>.35)&(cy<1.85)]
            frames=np.unique(geo['frame_ids'][evidence])
            if len(frames)<3:continue
            above=(abs(distance)<.055)&(u>lo+.03)&(u<hi-.03)&(y>1.85)&(y<3.)
            if above.sum()<30:continue
            heights=y[above];ybins=np.arange(1.85,3.02,.015);hist,_=np.histogram(heights,ybins)
            strong=np.where(gaussian_filter1d(hist.astype(float),1)>max(4.,hist.max()*.12))[0]
            if not len(strong):continue
            height=float(ybins[strong[0]])
            items.append({'id':f'geometric_opening_{len(items)+1}','surface_id':s['id'],'room_id':s['room_id'],'kind':'doorway',
                'surface_uv_bounds':[[float(lo),0.],[float(hi),height]],'width':measure(width,half_width=.05,method='wall_gap_and_transmitted_depth_rays'),
                'height':measure(height,half_width=.06,method='observed_lintel_on_wall_plane'),
                'status':'provisional_geometry_candidate','evidence':[f'depth_frame:{int(geo["indices"][f])}' for f in frames],
                'support_views':len(frames),'geometry_checks':{'rays_cross_wall_plane':True,'low_wall_occupancy':True,'observed_lintel':True}})
    return items


def merge_openings(geometric,visual):
    result=list(geometric)
    for v in visual:
        uv=np.mean(v['surface_uv_bounds'],axis=0)
        matching=next((g for g in geometric if g['surface_id']==v['surface_id'] and g['kind']==v['kind'] and abs(np.mean(g['surface_uv_bounds'],axis=0)[0]-uv[0])<.5),None)
        if matching:matching['evidence']+=v['evidence'];matching['visual_support']=True
        else:result.append(v)
    for i,o in enumerate(result):o['id']=f'opening_{i+1}'
    return result
