"""Public local models. No API calls, truth inputs, or color-to-damage rules."""
from pathlib import Path
import sys, time, json
import cv2
import numpy as np
from .io import sha256,write_json

ROOT=Path(__file__).resolve().parents[1]


class MetricDepth:
    def __init__(self,models=None,device='cpu',input_size=392):
        import torch
        self.torch=torch;torch.set_num_threads(4);self.device=device;self.size=input_size
        root=Path(models or ROOT/'models');source=root/'depth-anything-source'/'metric_depth';weights=root/'depth_anything_v2_metric_hypersim_vits.pth'
        if not source.exists() or not weights.exists():raise RuntimeError('Metric depth assets missing. Run: python scripts/fetch_models.py')
        sys.path.insert(0,str(source))
        from depth_anything_v2.dpt import DepthAnythingV2
        self.model=DepthAnythingV2(encoder='vits',features=64,out_channels=[48,96,192,384],max_depth=20).to(device)
        self.model.load_state_dict(torch.load(weights,map_location=device,weights_only=True));self.model.eval()
        self.fingerprint=sha256(weights);self.description={'name':'DepthAnythingV2-Metric-Hypersim-Small','weights_sha256':self.fingerprint,'device':device,'input_size':input_size,'license':'Apache-2.0'}
    def predict(self,bgr,cache=None):
        key=__import__('hashlib').sha256(bgr.tobytes()+f'{self.fingerprint}:{self.size}'.encode()).hexdigest()
        path=Path(cache)/(key+'.npy') if cache else None
        if path and path.exists():return np.load(path)
        with self.torch.inference_mode():d=self.model.infer_image(bgr,self.size)
        if path:path.parent.mkdir(parents=True,exist_ok=True);np.save(path,d)
        return d


class DepthPro:
    """Apple metric depth with its own focal estimate; entirely local inference."""
    def __init__(self,models=None,device='cpu'):
        import torch
        from dataclasses import replace
        self.torch=torch;torch.set_num_threads(4);self.device=device
        root=Path(models or ROOT/'models');source=root/'depth-pro-source'/'src';weights=root/'depth_pro.pt'
        if not source.exists() or not weights.exists():raise RuntimeError('Depth Pro assets missing. Run: python scripts/fetch_models.py --depth-pro')
        sys.path.insert(0,str(source))
        import depth_pro
        from depth_pro.depth_pro import DEFAULT_MONODEPTH_CONFIG_DICT
        cfg=replace(DEFAULT_MONODEPTH_CONFIG_DICT,checkpoint_uri=str(weights))
        self.model,self.preprocess=depth_pro.create_model_and_transforms(config=cfg,device=torch.device(device),precision=torch.float32)
        self.model.eval();self.fingerprint=sha256(weights)
        self.description={'name':'Apple Depth Pro','weights_sha256':self.fingerprint,'device':device,'license':'Apple supplied license','focal_method':'learned_from_image'}
    def predict_with_focal(self,bgr,cache=None):
        from PIL import Image
        key=__import__('hashlib').sha256(bgr.tobytes()+self.fingerprint.encode()).hexdigest()
        path=Path(cache)/(key+'.npz') if cache else None
        if path and path.exists():
            data=np.load(path);return data['depth'],float(data['focal'])
        image=Image.fromarray(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB))
        with self.torch.inference_mode():pred=self.model.infer(self.preprocess(image),f_px=None)
        d=pred['depth'].detach().cpu().numpy();f=float(pred['focallength_px'].detach().cpu())
        if path:path.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(path,depth=d,focal=f)
        return d,f


class Detector:
    def __init__(self,path=None,device='cpu'):
        import torch
        from transformers import AutoProcessor,AutoModelForZeroShotObjectDetection
        self.torch=torch;torch.set_num_threads(4);self.device=device
        path=Path(path or ROOT/'models/grounding-dino-tiny')
        if not path.exists():raise RuntimeError('Grounding DINO assets missing; run scripts/fetch_semantic_models.py')
        self.processor=AutoProcessor.from_pretrained(path,local_files_only=True)
        self.model=AutoModelForZeroShotObjectDetection.from_pretrained(path,local_files_only=True).to(device).eval()
        self.description={'name':'GroundingDINO-tiny','weights_sha256':sha256(path/'model.safetensors'),'device':device}
    def predict(self,bgr,text='door . doorway . window . wall crack . water damage . water stain .',threshold=.24):
        from PIL import Image
        key=__import__('hashlib').sha256(bgr.tobytes()+json.dumps([self.description,text,threshold],sort_keys=True).encode()).hexdigest()
        cache=ROOT/'.cache/detections'/f'{key}.json'
        if cache.exists():return json.loads(cache.read_text())
        image=Image.fromarray(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB))
        inputs=self.processor(images=image,text=text,return_tensors='pt').to(self.device)
        with self.torch.inference_mode():outputs=self.model(**inputs)
        result=self.processor.post_process_grounded_object_detection(outputs,inputs.input_ids,threshold=threshold,text_threshold=.22,target_sizes=[image.size[::-1]])[0]
        names=result.get('text_labels',result.get('labels',[]))
        candidates=[{'label':str(label),'score':float(score),'box':box.cpu().tolist(),'status':'unverified_candidate'} for label,score,box in zip(names,result['scores'],result['boxes'])]
        write_json(cache,candidates);return candidates


def focal_guess(image):
    """Estimate focal from orthogonal line vanishing points; fall back to a broad prior."""
    h,w=image.shape[:2];gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    lsd=cv2.createLineSegmentDetector();res=lsd.detect(gray)[0]
    prior=.85*max(w,h)
    if res is None:return prior,'broad_focal_prior'
    segments=res[:,0];length=np.linalg.norm(segments[:,2:]-segments[:,:2],axis=1);segments=segments[length>max(w,h)*.07]
    if len(segments)<10:return prior,'broad_focal_prior'
    lines=np.cross(np.c_[segments[:,:2],np.ones(len(segments))],np.c_[segments[:,2:],np.ones(len(segments))]);lines/=np.maximum(np.linalg.norm(lines[:,:2],axis=1,keepdims=True),1e-9)
    rng=np.random.default_rng(0);vps=[]
    for _ in range(300):
        a,b=rng.choice(len(lines),2,replace=False);v=np.cross(lines[a],lines[b])
        if abs(v[2])<1e-5:continue
        v=v/v[2];mid=(segments[:,:2]+segments[:,2:])/2;direc=segments[:,2:]-segments[:,:2];ray=v[:2]-mid
        cosine=abs(np.sum(direc*ray,axis=1))/(np.linalg.norm(direc,axis=1)*np.linalg.norm(ray,axis=1)+1e-9)
        support=np.sum(cosine>.998)
        if support>=4:vps.append((int(support),v[:2]))
    vps=sorted(vps,key=lambda a:-a[0]);kept=[]
    for _,v in vps:
        if all(np.linalg.norm(v-u)>max(w,h)*.3 for u in kept):kept.append(v)
        if len(kept)>=5:break
    values=[];c=np.array([w/2,h/2])
    for i,a in enumerate(kept):
        for b in kept[i+1:]:
            sq=-np.dot(a-c,b-c)
            if (.35*max(w,h))**2<sq<(1.8*max(w,h))**2:values.append(np.sqrt(sq))
    return (float(np.median(values)),'vanishing_point_candidate') if values else (prior,'broad_focal_prior')
