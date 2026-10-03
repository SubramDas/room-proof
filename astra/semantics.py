"""Surface association, proposal masks, openings, damage and traceable scope rules."""
from pathlib import Path
import cv2,numpy as np
from .layout import measure,point_in_poly
from .vision import Detector
from .io import write_json


def upright_rotation(pose):
    up=(pose[:3,:3].T@np.array([0.,1.,0.]))[:2]
    if np.linalg.norm(up)<.25:return 0
    options=[up,np.array([-up[1],up[0]]),-up,np.array([up[1],-up[0]])]
    return int(np.argmin([u[1] for u in options]))*90


def rotate_image(im,angle):
    if not angle:return im
    return cv2.rotate(im,{90:cv2.ROTATE_90_CLOCKWISE,180:cv2.ROTATE_180,270:cv2.ROTATE_90_COUNTERCLOCKWISE}[angle])


def inverse_pixels(uv,angle,w,h):
    x,y=np.asarray(uv,float).T
    if angle==90:return np.c_[y,h-1-x]
    if angle==180:return np.c_[w-1-x,h-1-y]
    if angle==270:return np.c_[w-1-y,x]
    return np.c_[x,y]


def ray_surface(uv,K,pose,surfaces,room_ids=None):
    origin=pose[:3,3];ray=pose[:3,:3]@np.linalg.solve(K,np.r_[uv,1.]);found=[]
    for s in surfaces:
        if s['kind']!='wall' or (room_ids is not None and s['room_id'] not in room_ids):continue
        a=np.array(s['start']);b=np.array(s['end']);e=b-a;length=np.linalg.norm(e)
        if length<.05:continue
        tangent=np.array([e[0],0,e[1]])/length;normal=np.array([-tangent[2],0,tangent[0]])
        anchor=np.array([a[0],s['floor_y'],a[1]]);den=float(ray@normal)
        if abs(den)<.08:continue
        t=float((anchor-origin)@normal/den)
        if t<=0:continue
        p=origin+t*ray;u=float((p-anchor)@tangent);v=float(p[1]-s['floor_y']);height=s['height']['value']
        if -.15<=u<=length+.15 and -.15<=v<=(height or 4)+.15:found.append((float(np.linalg.norm(p-origin)),s,p,np.array([u,v])))
    return min(found,key=lambda x:x[0]) if found else None


def on_surface(uv,K,pose,surface):
    a=np.array(surface['start']);b=np.array(surface['end']);edge=b-a;L=np.linalg.norm(edge);tangent=np.r_[edge[0],0,edge[1]]/L
    n=np.array([-tangent[2],0,tangent[0]]);origin=pose[:3,3];anchor=np.array([a[0],surface['floor_y'],a[1]])
    rays=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T@pose[:3,:3].T;den=rays@n
    good=abs(den)>.08;t=np.full(len(uv),np.nan);t[good]=((anchor-origin)@n)/den[good];good&=t>0
    points=origin+rays*t[:,None];su=(points-anchor)@tangent;sv=points[:,1]-surface['floor_y']
    return np.c_[su,sv],good


def mask_for_box(image,box):
    h,w=image.shape[:2];x1,y1,x2,y2=np.rint(box).astype(int);x1,y1=max(0,x1),max(0,y1);x2,y2=min(w-1,x2),min(h-1,y2)
    if x2-x1<4 or y2-y1<4:return None
    mask=np.zeros((h,w),np.uint8)
    try:
        cv2.grabCut(image,mask,(x1,y1,x2-x1,y2-y1),np.zeros((1,65)),np.zeros((1,65)),3,cv2.GC_INIT_WITH_RECT)
        mask=np.uint8((mask==1)|(mask==3))*255
    except cv2.error:mask[y1:y2,x1:x2]=255
    return mask


def staged_regions(image):
    """Explicit benchmark-marker mode, never enabled in general damage detection."""
    hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV);h,w=hsv.shape[:2];results=[]
    # The user's colored props are declared staging, so this mode assesses their
    # projection/extent only and must not be scored as natural-damage recognition.
    ranges=[('staged_crack_marker',(0,0,0),(179,255,55)),('staged_flood_marker',(5,65,40),(30,230,190))]
    for label,lo,hi in ranges:
        mask=cv2.inRange(hsv,np.array(lo),np.array(hi));mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
        contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area=cv2.contourArea(c);x,y,bw,bh=cv2.boundingRect(c)
            if not .001*h*w<area<.055*h*w or min(bw,bh)<12:continue
            approx=cv2.approxPolyDP(c,.025*cv2.arcLength(c,True),True)
            if not 4<=len(approx)<=6 or area/(bw*bh)<.7:continue
            results.append({'label':label,'score':None,'box':[x,y,x+bw,y+bh],'status':'staging_marker_candidate','contour':c[:,0].tolist()})
    return results


def run_semantics(views,layout,out,device='cpu',max_views=12,staged=False,enabled=True):
    out=Path(out);(out/'overlays').mkdir(parents=True,exist_ok=True);all_candidates=[];openings=[];damage=[];warnings=[]
    detector=None
    if enabled:
        try:detector=Detector(device=device)
        except Exception as e:warnings.append(f'Semantic model unavailable: {type(e).__name__}: {e}')
    for vi in np.unique(np.linspace(0,len(views)-1,min(max_views,len(views)),dtype=int)):
        v=views[vi];raw=v['bgr'];pose=v.get('pose');K=v.get('K');angle=upright_rotation(pose) if pose is not None else 0
        image=rotate_image(raw,angle);h,w=raw.shape[:2];candidates=detector.predict(image) if detector else []
        if staged:candidates+=staged_regions(image)
        overlay=image.copy()
        for c in candidates:
            c={**c,'view_id':str(v.get('id',vi)),'source':v.get('source',v.get('image')),'rotation':angle};box=c['box'];x1,y1,x2,y2=box
            corners=inverse_pixels([[x1,y1],[x2,y1],[x2,y2],[x1,y2]],angle,w,h)
            centre=corners.mean(0);hit=ray_surface(centre,K,pose,layout['surfaces'],v.get('room_ids')) if pose is not None else None
            label=c['label'].lower();is_open=any(t in label for t in ['door','window','opening']);is_damage=any(t in label for t in ['crack','water','stain','flood'])
            cv2.rectangle(overlay,(int(x1),int(y1)),(int(x2),int(y2)),(0,180,255),2)
            cv2.putText(overlay,c['label'],(int(x1),max(15,int(y1)-4)),cv2.FONT_HERSHEY_SIMPLEX,.4,(0,0,255),1)
            if hit:
                _,s,p,suv=hit;uv,good=on_surface(corners,K,pose,s)
                c['surface_id']=s['id'];c['surface_uv_box']=uv.tolist() if good.all() else None
                if good.all():
                    low=uv.min(0);high=uv.max(0);width,height=high-low
                    if is_open and .35<width<3.5 and .5<height<3.5:
                        kind='window' if 'window' in label else 'doorway';candidate={'id':f'opening_{len(openings)+1}','surface_id':s['id'],'room_id':s['room_id'],'kind':kind,
                            'surface_uv_bounds':[low.tolist(),high.tolist()],'width':measure(width,half_width=max(.08,width*.12)),
                            'height':measure(height,half_width=max(.08,height*.12)),'status':'provisional_visual_candidate','evidence':[c['source']],'support_views':1}
                        duplicate=next((o for o in openings if o['surface_id']==s['id'] and np.linalg.norm(np.mean(o['surface_uv_bounds'],axis=0)-(low+high)/2)<.4),None)
                        if duplicate:duplicate['support_views']+=1;duplicate['evidence'].append(c['source'])
                        else:openings.append(candidate)
                    if is_damage:
                        mask=mask_for_box(image,box)
                        if 'contour' in c:
                            mask=np.zeros(image.shape[:2],np.uint8);cv2.fillPoly(mask,[np.array(c['contour'],np.int32)],255)
                        if mask is not None:
                            contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
                            if contours:
                                contour=max(contours,key=cv2.contourArea)[:,0];contour=contour[::max(1,len(contour)//300)];rawuv=inverse_pixels(contour,angle,w,h);metric,valid=on_surface(rawuv,K,pose,s)
                                if valid.all():
                                    area=abs(float(cv2.contourArea(metric.astype(np.float32))));cls='crack' if 'crack' in label else 'water_logging/floods'
                                    damage.append({'id':f'damage_{len(damage)+1}','surface_id':s['id'],'room_id':s['room_id'],'class':cls,
                                        'surface_polygon':metric.tolist(),'area':measure(area,'m2',half_width=max(.01,area*.4)),
                                        'extent_width':measure(float(np.ptp(metric[:,0])),half_width=max(.05,width*.15)),
                                        'extent_height':measure(float(np.ptp(metric[:,1])),half_width=max(.05,height*.15)),
                                        'crack_length':measure(None) if cls=='crack' else None,'evidence':[c['source']],
                                        'status':'staged_marker_assessment' if 'staged' in label else 'unverified_visual_damage',
                                        'class_score':c['score'],'observed_polygon_not_confirmed_hidden_extent':True})
            c.pop('contour',None);all_candidates.append(c)
        cv2.imwrite(str(out/'overlays'/f'{vi:04d}.jpg'),overlay)
        print(f'Semantics {vi+1}/{len(views)}: {len(candidates)} candidates',flush=True)
    # Surface raster union merges repeated views, preserving one region per class/surface.
    merged=[]
    for sid,cls in sorted({(d['surface_id'],d['class']) for d in damage}):
        ds=[d for d in damage if d['surface_id']==sid and d['class']==cls];alluv=np.concatenate([d['surface_polygon'] for d in ds]);origin=alluv.min(0);span=alluv.max(0)-origin
        cell=max(.005,float(span.max()/1200));size=np.ceil(span/cell).astype(int)+3;mask=np.zeros((size[1],size[0]),np.uint8)
        for d in ds:cv2.fillPoly(mask,[np.rint((np.array(d['surface_polygon'])-origin)/cell).astype(np.int32)],1)
        contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            poly=contour[:,0]*cell+origin;area=float(cv2.contourArea(contour)*cell*cell)
            if area<=0:continue
            item={**ds[0],'id':f'damage_{len(merged)+1}','surface_polygon':poly.tolist(),'area':measure(area,'m2',half_width=max(.01,area*.4)),
                  'evidence':sorted({e for d in ds for e in d['evidence']})};merged.append(item)
    write_json(out/'candidates.json',{'candidates':all_candidates,'warnings':warnings,'detector':detector.description if detector else None,'staged_mode':staged})
    return openings,merged,warnings


def scope_and_flags(damage,surfaces):
    flags=[];scope=[];index={s['id']:s for s in surfaces}
    for d in damage:
        s=index[d['surface_id']];s['damage_ids'].append(d['id'])
        if d['status']=='staged_marker_assessment':
            scope.append({'id':f'scope_{len(scope)+1}','surface_id':s['id'],'damage_id':d['id'],'action':'inspect_staged_region_demo','quantity':d['area'],'provisional':True,'rule':'STAGED_DEMO_ONLY_v1'})
            continue
        scope.append({'id':f'scope_{len(scope)+1}','surface_id':s['id'],'damage_id':d['id'],'action':'inspect_visible_damage_before_repair','quantity':d['area'],'provisional':True,'rule':'VISIBLE_REGION_INSPECTION_v1'})
        uv=np.array(d['surface_polygon']);length=np.linalg.norm(np.array(s['end'])-s['start']);edge=bool(uv[:,0].min()<.05 or uv[:,0].max()>length-.05)
        if edge:
            flags.append({'id':f'flag_{len(flags)+1}','surface_id':s['id'],'damage_id':d['id'],'rule':'VISIBLE_DAMAGE_AT_SURFACE_EDGE_v1',
                'rule_inputs':{'edge_tolerance_m':.05,'class':d['class'],'surface_visibility':s['visibility']},
                'message':'Visible region reaches surface boundary; inspect adjoining or hidden area. Hidden damage is not confirmed.',
                'status':'inspection_recommendation','evidence':d['evidence']})
    return scope,flags
