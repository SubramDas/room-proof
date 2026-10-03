"""Reconstruct identical selected frames with correction enabled and disabled."""
import os,sys,argparse,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
from astra.lidar import reconstruct
from astra.layout import build_layout
from astra.io import write_json
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('--input',default='three_room/lidar');p.add_argument('--output',default='runs/drift_ablation');p.add_argument('--max-frames',type=int,default=140);a=p.parse_args()
out=Path(a.output);out.mkdir(parents=True,exist_ok=True);fig,ax=plt.subplots(figsize=(10,7));summary={}
for enabled,color in [(False,'#dc6b25'),(True,'#2463b3')]:
    mode='on' if enabled else 'off';t=time.perf_counter();g=reconstruct(a.input,out/mode,a.max_frames,enabled);l=build_layout(g);l.pop('raster');write_json(out/mode/'layout.json',l)
    ps=np.concatenate([r['polygon'] for r in l['rooms']]);extent=np.ptp(ps,axis=0);area=sum(r['floor_area']['value'] for r in l['rooms'])
    summary[mode]={'room_count':len(l['rooms']),'summed_room_area_m2':area,'axis_extent_m':extent,'runtime_s':time.perf_counter()-t,'correction':g['drift']}
    for i,r in enumerate(l['rooms']):
        q=np.array(r['polygon']);q=np.r_[q,q[:1]];ax.plot(q[:,0],q[:,1],color=color,label='drift '+mode if i==0 else None,alpha=.8)
    q=g['poses'][:,:3,3];ax.plot(q[:,0],q[:,2],color=color,alpha=.3,linewidth=.7)
summary['interpretation']='Observed change, not proof of improved truth accuracy. Same source frames are not repeat captures.'
summary['area_change_m2']=summary['on']['summed_room_area_m2']-summary['off']['summed_room_area_m2'];write_json(out/'ablation.json',summary)
ax.set_aspect('equal');ax.grid(alpha=.3);ax.legend();ax.set(xlabel='x (m)',ylabel='z (m)',title='Drift correction ablation — same raw capture');fig.tight_layout();fig.savefig(out/'footprint_comparison.png',dpi=140);fig.savefig(out/'footprint_comparison.svg');print(out)
