"""Room extraction from observed free space; reference dimensions never enter here."""
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter, maximum_filter, label, binary_fill_holes
from .geometry import plane_modes


def measure(value,unit='m',half_width=None,method='geometry',status='estimated'):
    if value is None:return {'value':None,'unit':unit,'interval':{'level':.95,'lower':None,'upper':None,'calibration_status':'unavailable'},'status':'unobserved','method':method}
    v=float(value);h=float(half_width if half_width is not None else max(.04,abs(v)*.025))
    return {'value':v,'unit':unit,'interval':{'level':.95,'lower':max(0.,v-h),'upper':v+h,'calibration_status':'provisional_not_empirically_calibrated'},'status':status,'method':method}


def polygon_area(poly):
    a=np.asarray(poly);return abs(float(np.dot(a[:,0],np.roll(a[:,1],1))-np.dot(a[:,1],np.roll(a[:,0],1)))/2)


def point_in_poly(point,poly):return cv2.pointPolygonTest(np.asarray(poly,np.float32),tuple(map(float,point)),False)>=0


def build_layout(geo,tier='lidar',single_room=False,room_names=None,cell=.04,method='planes'):
    p=geo['points'];n=geo['normals'];poses=geo['poses'];fids=geo['frame_ids'];cam=poses[:,:3,3]
    if len(p)<100:raise ValueError('Insufficient geometry for a room layout')
    horizontal=abs(n[:,1])>.92;hm=plane_modes(p[horizontal,1]);camera_y=float(np.median(cam[:,1]))
    below=[v for v in hm if v<camera_y-.45];above=[v for v in hm if v>camera_y+.4]
    # Prefer supported outer planes; tiny horizontal objects cannot become the floor.
    support=lambda y:int(np.sum(horizontal&(abs(p[:,1]-y)<.045)))
    floor=max(below,key=support) if below else float(np.quantile(p[:,1],.02))
    ceiling=max(above,key=support) if above else None
    bounds=np.quantile(p[:,[0,2]],[.003,.997],axis=0);origin=bounds[0]-.25;size=np.ceil((bounds[1]-origin+.25)/cell).astype(int)
    if max(size)>1600:raise ValueError('Geometry extent too large; check units/poses')
    free=np.zeros((size[1],size[0]),np.uint8);hits=np.zeros_like(free,dtype=np.float32)
    def grid(q):return np.rint((q-origin)/cell).astype(int)
    # Free-space rays at torso height avoid using cupboards as exterior boundaries.
    band=(p[:,1]>floor+.95)&(p[:,1]<floor+1.85)
    ids=np.where(band)[0][::5]
    for k in ids:
        a=grid(cam[fids[k],[0,2]]);b=grid(p[k,[0,2]])
        if np.all(a>=0) and np.all(a<size) and np.all(b>=0) and np.all(b<size):cv2.line(free,tuple(a),tuple(b),1,1)
    floorpts=p[(abs(p[:,1]-floor)<.07)&horizontal][:,[0,2]];g=grid(floorpts)
    valid=(g>=0).all(1)&(g<size).all(1);g=g[valid];free[g[:,1],g[:,0]]=1
    walls=(abs(n[:,1])<.25)&(p[:,1]>floor+.25)&(p[:,1]<floor+2.3)
    g=grid(p[walls][:,[0,2]]);valid=(g>=0).all(1)&(g<size).all(1);g=g[valid];np.add.at(hits,(g[:,1],g[:,0]),1)
    free=cv2.morphologyEx(free,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8));free=binary_fill_holes(free).astype(np.uint8)
    free=cv2.morphologyEx(free,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    num,components,stats,_=cv2.connectedComponentsWithStats(free)
    for k in range(1,num):
        if stats[k,cv2.CC_STAT_AREA]*cell*cell<.3:free[components==k]=0
    dist=cv2.distanceTransform(free,cv2.DIST_L2,5)*cell;smooth=gaussian_filter(dist,2)
    peaks=(smooth==maximum_filter(smooth,size=max(9,int(.9/cell))))&(smooth>.25)
    lab,count=label(peaks);seeds=[]
    for k in range(1,count+1):
        yy,xx=np.where(lab==k);idx=np.argmax(smooth[yy,xx]);seeds.append((int(xx[idx]),int(yy[idx]),float(smooth[yy[idx],xx[idx]])))
    seeds=sorted(seeds,key=lambda x:-x[2]);retained=[]
    for seed in seeds:
        if all(np.linalg.norm(np.array(seed[:2])-q[:2])*cell>max(.8,.8*(seed[2]+q[2])) for q in retained):retained.append(seed)
    if not retained:
        y,x=np.unravel_index(np.argmax(dist),dist.shape);retained=[(int(x),int(y),float(dist[y,x]))]
    # Watershed basins yield candidate spaces; uncertain subdivisions stay visible in QA.
    markers=np.zeros(free.shape,np.int32);markers[free==0]=1
    for i,(x,y,_) in enumerate(retained):cv2.circle(markers,(x,y),2,i+2,-1)
    height=np.uint8(np.clip(255*(1-smooth/max(smooth.max(),1e-6)),0,255));image=cv2.cvtColor(height,cv2.COLOR_GRAY2BGR)
    # Flood the scalar distance surface itself (OpenCV watershed instead floods
    # image gradients and can trap the seed in a tiny plateau).
    import heapq
    segmented=np.where(free==0,1,0).astype(np.int32);heap=[];serial=0
    for i,(x,y,_) in enumerate(retained):
        segmented[y,x]=i+2;heapq.heappush(heap,(-float(smooth[y,x]),serial,y,x,i+2));serial+=1
    while heap:
        level,_,y,x,k=heapq.heappop(heap)
        for yy,xx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
            if yy<0 or xx<0 or yy>=free.shape[0] or xx>=free.shape[1] or segmented[yy,xx]!=0:continue
            segmented[yy,xx]=k;heapq.heappush(heap,(max(level,-float(smooth[yy,xx])),serial,yy,xx,k));serial+=1
    candidates=[]
    modes={axis:plane_modes(p[(abs(n[:,axis])>.94)&(p[:,1]>floor+.6),axis]) for axis in [0,2]}
    for i,seed in enumerate(retained):
        mask=np.uint8(segmented==i+2)
        if mask.sum()*cell*cell<.45:continue
        contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        if not contours:continue
        contour=max(contours,key=cv2.contourArea);contour=cv2.approxPolyDP(contour,2.0,True)[:,0,:]
        poly=contour*cell+origin
        if len(poly)<3:continue
        area=polygon_area(poly)
        if method=='planes':
            seed_world=(poly.min(0)+poly.max(0))/2;enclosing=[]
            # High wall observations reject most tables/counters and are present
            # above door openings, where the free-space bottleneck is ambiguous.
            for axis,other,centre,across in [(0,2,seed_world[0],seed_world[1]),(2,0,seed_world[1],seed_world[0])]:
                wall_band=(abs(n[:,axis])>.95)&(p[:,1]>floor+1.85)&(abs(p[:,other]-across)<1.2)
                vals=plane_modes(p[wall_band,axis]);left=[v for v in vals if v<centre-.25];right=[v for v in vals if v>centre+.25]
                enclosing.append((max(left),min(right)) if left and right else None)
            if all(e is not None for e in enclosing):
                (x0,x1),(z0,z1)=enclosing;boxarea=(x1-x0)*(z1-z0)
                # Only replace a basin with plausible observed enclosing walls.
                if .4<boxarea<40 and .55<boxarea/max(area,1e-6)<2.5:
                    poly=np.array([[x0,z0],[x1,z0],[x1,z1],[x0,z1]]);area=polygon_area(poly)
        # Infer a rectangle only where observed polygon strongly supports it.
        lo=poly.min(0);hi=poly.max(0);rect_area=float(np.prod(hi-lo));rectangularity=area/max(rect_area,1e-6)
        if rectangularity>.84:
            for k,axis in enumerate([0,2]):
                for val,side in [(lo[k],'lo'),(hi[k],'hi')]:
                    near=[v for v in modes[axis] if abs(v-val)<.16]
                    if near:
                        v=min(near,key=lambda q:abs(q-val))
                        if side=='lo':lo[k]=v
                        else:hi[k]=v
            poly=np.array([[lo[0],lo[1]],[hi[0],lo[1]],[hi[0],hi[1]],[lo[0],hi[1]]]);area=polygon_area(poly)
        visits=[j for j,q in enumerate(cam[:,[0,2]]) if point_in_poly(q,poly)]
        candidates.append({'polygon':poly.tolist(),'area':area,'visits':visits,'seed':seed,'rectangularity':rectangularity})
    if single_room and candidates:candidates=[max(candidates,key=lambda c:(len(c['visits']),c['area']))]
    candidates.sort(key=lambda c:(min(c['visits']) if c['visits'] else 1e9,-c['area']))
    rooms=[];surfaces=[];sigma=.04 if tier=='lidar' else .25
    for i,c in enumerate(candidates):
        rid=room_names[i] if room_names and i<len(room_names) else f'room_{i+1}'
        poly=np.array(c['polygon']);lo=poly.min(0);hi=poly.max(0)
        inside=(p[:,0]>=lo[0])&(p[:,0]<=hi[0])&(p[:,2]>=lo[1])&(p[:,2]<=hi[1])
        local_h=plane_modes(p[inside&horizontal&(p[:,1]>floor+1.8),1]);ceil=ceiling
        if local_h:ceil=max(local_h,key=lambda y:np.sum(inside&horizontal&(abs(p[:,1]-y)<.045)))
        local_floor=floor
        if method=='planes':
            local_floor_modes=plane_modes(p[inside&horizontal&(p[:,1]<camera_y-.45),1])
            if local_floor_modes:
                local_floor=max(local_floor_modes,key=lambda y:np.sum(inside&horizontal&(abs(p[:,1]-y)<.045)))
        h=ceil-local_floor if ceil is not None else None
        walls=[]
        for j,(a,b) in enumerate(zip(poly,np.roll(poly,-1,axis=0))):
            sid=f'{rid}_wall_{j+1}';length=float(np.linalg.norm(b-a))
            edge={'surface_id':sid,'start':a.tolist(),'end':b.tolist(),'length':measure(length,half_width=max(sigma,length*(.025 if tier=='lidar' else .18)))}
            walls.append(edge);surfaces.append({'id':sid,'room_id':rid,'kind':'wall','start':a.tolist(),'end':b.tolist(),'floor_y':float(local_floor),
                'height':measure(h,half_width=.05 if tier=='lidar' else .45),'gross_area':measure(length*h if h else None,'m2',half_width=max(.1,length*(h or 0)*(.06 if tier=='lidar' else .4))),
                'visibility':'partial','damage_ids':[]})
        for kind in ['floor','ceiling']:
            surfaces.append({'id':f'{rid}_{kind}','room_id':rid,'kind':kind,'polygon':poly.tolist(),'y':float(local_floor) if kind=='floor' else (float(ceil) if ceil is not None else None),
                'gross_area':measure(c['area'],'m2',half_width=c['area']*(.07 if tier=='lidar' else .4)),'visibility':'partial','damage_ids':[]})
        rooms.append({'id':rid,'name':rid,'polygon':poly.tolist(),'walls':walls,'floor_y':float(local_floor),'ceiling_y':float(ceil) if ceil is not None else None,
            'ceiling_height':measure(h,half_width=.05 if tier=='lidar' else .45),'floor_area':measure(c['area'],'m2',half_width=c['area']*(.07 if tier=='lidar' else .4)),
            'extent_x':measure(hi[0]-lo[0],half_width=sigma if tier=='lidar' else .4),'extent_z':measure(hi[1]-lo[1],half_width=sigma if tier=='lidar' else .4),
            'camera_visits':c['visits'],'status':'provisional','geometry_source':'observed_free_space_and_planes'})
    qa={'floor_y':float(floor),'method':method,'ceiling_y':ceiling,'horizontal_plane_modes':hm,'room_candidate_count':len(candidates),
        'warnings':['Room boundaries and interval calibration are provisional.','Watershed spaces require topology validation; no declared room count is forced.']}
    return {'rooms':rooms,'surfaces':surfaces,'adjacency':[],'openings':[],'layout_qa':qa,'raster':{'free':free,'hits':hits,'segments':segmented,'origin':origin,'cell':cell}}
