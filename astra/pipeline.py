from pathlib import Path
import json,os,platform,subprocess,time,resource
import cv2,numpy as np
from . import __version__
from .io import write_json,input_manifest,selected_video,sha256
from .lidar import reconstruct
from .layout import build_layout,point_in_poly
from .rgb import reconstruct_rgb
from .semantics import run_semantics,scope_and_flags
from .schema import validate
from .export import render
from .quality import topology_quality
from .openings import geometric_openings,merge_openings


def code_revision():
    try:return subprocess.check_output(['git','--git-dir=.history','--work-tree=.','rev-parse','HEAD'],stderr=subprocess.DEVNULL,text=True).strip()
    except Exception:return 'unversioned'


def offset_layout(layout,offset,prefix):
    ids={s['id']:prefix+s['id'] for s in layout['surfaces']}
    for room in layout['rooms']:
        room['id']=prefix+room['id'];room['name']=room['id'];room['polygon']=(np.array(room['polygon'])+offset).tolist()
        for w in room['walls']:
            w['surface_id']=ids[w['surface_id']];w['start']=(np.array(w['start'])+offset).tolist();w['end']=(np.array(w['end'])+offset).tolist()
    for s in layout['surfaces']:
        s['id']=ids[s['id']];s['room_id']=prefix+s['room_id']
        if s['kind']=='wall':s['start']=(np.array(s['start'])+offset).tolist();s['end']=(np.array(s['end'])+offset).tolist()
        else:s['polygon']=(np.array(s['polygon'])+offset).tolist()


def adjacency_from_openings(layout):
    """Paired openings on facing room boundaries; no hard-coded room graph."""
    surfaces={s['id']:s for s in layout['surfaces']};edges=[]
    for i,a in enumerate(layout['openings']):
        if a['kind']!='doorway':continue
        sa=surfaces[a['surface_id']];aa=np.array(sa['start']);ab=np.array(sa['end']);ea=(ab-aa)/np.linalg.norm(ab-aa)
        ua=float(np.mean(np.array(a['surface_uv_bounds'])[:,0]));center=aa+ea*ua
        for b in layout['openings'][i+1:]:
            if b['room_id']==a['room_id'] or b['kind']!='doorway':continue
            sb=surfaces[b['surface_id']];ba=np.array(sb['start']);bb=np.array(sb['end']);eb=(bb-ba)/np.linalg.norm(bb-ba)
            ub=float(np.mean(np.array(b['surface_uv_bounds'])[:,0]));cb=ba+eb*ub
            if abs(ea@eb)>.95 and np.linalg.norm(center-cb)<.35 and abs(a['width']['value']-b['width']['value'])<.25:
                edge={'rooms':sorted([a['room_id'],b['room_id']]),'opening_ids':[a['id'],b['id']],'status':'provisional_paired_openings'}
                if not any(e['rooms']==edge['rooms'] for e in edges):edges.append(edge)
    return edges


def run(args):
    start=time.perf_counter();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    source_root=Path(__file__).resolve().parents[1]
    start_revision=code_revision()
    source_hashes={str(p.relative_to(source_root)):sha256(p) for p in sorted((source_root/'astra').glob('*.py'))}
    write_json(out/'source_manifest_at_start.json',{'revision':start_revision,'files':source_hashes})
    write_json(out/'run_status.json',{'status':'running','tier':args.tier})
    warnings=['Official evaluator schema unavailable; validated against astra.provisional.v1.',
        'Intervals are engineering ranges, not empirically calibrated confidence intervals.']
    views=[];files=[];extra={};geometry_openings=[]
    if args.tier=='lidar':
        g=reconstruct(args.input,out/'geometry',args.max_frames,args.drift=='on',min_confidence=args.min_confidence,gravity_lock=args.gravity_lock);layout=build_layout(g,single_room=args.single_room,method=args.layout_method)
        geometry_openings=geometric_openings(g,layout['surfaces'])
        raster=layout.pop('raster');np.savez_compressed(out/'layout_raster.npz',**raster)
        extra={'drift':g['drift'],'quality':g['qa']};indices=g['indices'];scan=g['scan']
        visual_ids=np.unique(np.linspace(0,len(indices)-1,min(args.semantic_views,len(indices)),dtype=int))
        frames=selected_video(scan['root']/'rgb.mp4',indices[visual_ids],out/'keyframes')
        for pos,v in zip(visual_ids,frames):
            im=cv2.imread(v['image']);K=g['K'][pos].copy();K[0]*=im.shape[1]/scan['video']['width'];K[1]*=im.shape[0]/scan['video']['height']
            views.append({'id':int(indices[pos]),'bgr':im,'pose':g['poses'][pos],'K':K,'source':f"rgb.mp4#frame={indices[pos]}",
                          'sensor_depth':cv2.imread(str(scan['root']/'depth'/f"{scan['ids'][indices[pos]]}.png"),cv2.IMREAD_UNCHANGED).astype(np.float32)*.001,
                          'sensor_confidence':cv2.imread(str(scan['root']/'confidence'/f"{scan['ids'][indices[pos]]}.png"),cv2.IMREAD_UNCHANGED)})
        files=[scan['root']/n for n in ['odometry.csv','imu.csv','camera_matrix.csv','rgb.mp4']]
        files+=list((scan['root']/'depth').glob('*.png'))+list((scan['root']/'confidence').glob('*.png'));base=scan['root']
        warnings+=g['qa']['warnings']+layout['layout_qa']['warnings']
    else:
        components,views,summary=reconstruct_rgb(args.input,args.tier,out/'geometry',device=args.device,max_frames=args.max_frames,rotation=args.rotation,depth_model=args.depth_model,geometry_bridges=args.rgb_geometry_bridges,scale_refinement=args.rgb_scale_refinement)
        layout={'rooms':[],'surfaces':[],'openings':[],'adjacency':[]};cursor=0.;component_offsets={}
        if args.tier=='photos':
            # One output room per source folder; choose its best-supported component.
            # A disconnected extra view must not create a duplicate physical room.
            for room_name in sorted({v['room_hint'] for v in views}):
                roomviews=[v for v in views if v['room_hint']==room_name]
                counts={c:sum(v['component']==c for v in roomviews) for c in {v['component'] for v in roomviews}}
                ci=max(counts,key=counts.get);g=components[ci];ids=[i for i in g['view_ids'] if views[i]['room_hint']==room_name]
                selected=[g['view_ids'].index(i) for i in ids];mask=np.isin(g['frame_ids'],selected)
                remap={old:new for new,old in enumerate(selected)}
                local={'points':g['points'][mask],'normals':g['normals'][mask],'frame_ids':np.array([remap[int(i)] for i in g['frame_ids'][mask]]),
                       'poses':g['poses'][selected]}
                try:part=build_layout(local,args.tier,single_room=True,room_names=[room_name],method=args.layout_method)
                except ValueError as e:warnings.append(f'{room_name}: {e}');continue
                part.pop('raster')
                if ci not in component_offsets:
                    low=min([np.min(np.array(r['polygon'])[:,0]) for r in part['rooms']]+[0.]);component_offsets[ci]=np.array([cursor-low,0.])
                offset=component_offsets[ci];offset_layout(part,offset,'')
                for vi in ids:
                    views[vi]['pose'][0,3]+=offset[0];views[vi]['pose'][2,3]+=offset[1];views[vi]['room_ids']=[r['id'] for r in part['rooms']]
                for v in roomviews:
                    if v['id'] not in ids:v['pose']=None;v['room_ids']=[]
                layout['rooms']+=part['rooms'];layout['surfaces']+=part['surfaces'];cursor=max([np.max(np.array(r['polygon'])[:,0]) for r in part['rooms']]+[cursor])+1.
        else:
            for ci,g in enumerate(components):
                try:part=build_layout(g,args.tier,single_room=args.single_room,method=args.layout_method)
                except ValueError as e:warnings.append(f'Component {ci}: {e}');continue
                part.pop('raster');low=min([np.min(np.array(r['polygon'])[:,0]) for r in part['rooms']]+[0.]);offset=np.array([cursor-low,0.])
                offset_layout(part,offset,f'component_{ci+1}_' if len(components)>1 else '')
                for vi in g['view_ids']:
                    views[vi]['pose'][0,3]+=offset[0];views[vi]['pose'][2,3]+=offset[1];views[vi]['room_ids']=[r['id'] for r in part['rooms']]
                layout['rooms']+=part['rooms'];layout['surfaces']+=part['surfaces'];cursor=max([np.max(np.array(r['polygon'])[:,0]) for r in part['rooms']]+[cursor])+1.
        if len(components)>1:warnings.append(f'{len(components)} disconnected RGB components placed schematically; physical stitching is unresolved.')
        extra={'rgb_reconstruction':summary};warnings+=summary['warnings']
        if args.tier=='photos':files=[v['image'] for v in views];base=Path(args.input)
        else:files=[Path(args.input)];base=Path(args.input).parent
    if not layout['rooms']:warnings.append('No room could be reconstructed from the observed geometry.')
    opens,damage,semantic_warnings=run_semantics(views,layout,out/'semantics',args.device,args.semantic_views,args.staged_damage,args.semantics=='on')
    opens=merge_openings(geometry_openings,opens);layout['openings']=opens;layout['adjacency']=adjacency_from_openings(layout)
    scope,flags=scope_and_flags(damage,layout['surfaces']);warnings+=semantic_warnings
    topology=topology_quality(layout['rooms'],layout['adjacency'],args.tier,physical_stitch=args.tier=='lidar' or len(components)==1)
    if topology['status']=='unresolved_physical_stitch':warnings.append('Physical whole-property stitch unresolved: inspect connectivity, component placement and overlaps.')
    if args.staged_damage:warnings.append('Explicit staging-marker mode: not a benchmark of natural crack/flood recognition.')
    result={'schema_version':'astra.provisional.v1','capture_id':args.capture_id or Path(args.input).stem,'tier':args.tier,
        'status':'provisional_reconstruction' if layout['rooms'] else 'unresolved_geometry',
        'layout_quality':topology,'rooms':layout['rooms'],'surfaces':layout['surfaces'],'openings':opens,'adjacency':layout['adjacency'],'damage':damage,
        'concealed_damage_flags':flags,'scope_items':scope,'warnings':warnings,'diagnostics':extra}
    validate(result,args.schema);write_json(out/'result.json',result);render(result,out)
    manifest=input_manifest(files,base);write_json(out/'input_manifest.json',manifest)
    import importlib.metadata
    dependencies={}
    for package in ['numpy','scipy','opencv-python-headless','torch','torchvision','transformers','timm','matplotlib','imageio-ffmpeg']:
        try:dependencies[package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:pass
    provenance={'source_hashes':source_hashes,'dependencies':dependencies,'semantic_model_manifest':'semantics/candidates.json','version':__version__,'code_revision':start_revision,'config':vars(args),'platform':platform.platform(),
        'python':platform.python_version(),'input_root':str(Path(base).resolve()),'input_manifest':'input_manifest.json',
        'wall_time_seconds':time.perf_counter()-start,'max_rss_mb':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        'ground_truth_used_for_inference':False,'intervals_calibrated':False,'models':extra.get('rgb_reconstruction',{}).get('model',None)}
    write_json(out/'provenance.json',provenance);write_json(out/'run_status.json',{'status':'complete_with_limitations','result':'result.json','runtime_seconds':provenance['wall_time_seconds']})
    print(f"Output: {out/'report.html'} ({provenance['wall_time_seconds']:.1f}s)",flush=True)
    return result
