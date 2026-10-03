import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
os.environ.setdefault('HF_HOME',str(ROOT/'.cache/huggingface'))
os.environ.setdefault('OPENBLAS_NUM_THREADS','4')
os.environ.setdefault('OMP_NUM_THREADS','4')
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
import argparse,json,sys
from .io import write_json


def main():
    p=argparse.ArgumentParser(prog='astra',description='Local property reconstruction and evidence-linked assessment')
    sub=p.add_subparsers(dest='action',required=True)
    r=sub.add_parser('run');r.add_argument('--tier',choices=['lidar','photos','video'],required=True);r.add_argument('--input',required=True);r.add_argument('--output',required=True)
    r.add_argument('--depth-model',choices=['small','depth-pro','depth-pro-int8'],default='small');r.add_argument('--layout-method',choices=['planes','free-space'],default='planes');r.add_argument('--capture-id');r.add_argument('--max-frames',type=int,default=120);r.add_argument('--single-room',action='store_true');r.add_argument('--drift',choices=['on','off'],default='on')
    r.add_argument('--semantics',choices=['on','off'],default='on');r.add_argument('--semantic-views',type=int,default=10);r.add_argument('--device',choices=['cpu','cuda'],default='cpu')
    r.add_argument('--rotation',type=int,choices=[0,90,180,270],default=0);r.add_argument('--staged-damage',action='store_true');r.add_argument('--schema',help='Optional official evaluator JSON schema')
    a=sub.add_parser('audit');a.add_argument('--input',required=True);a.add_argument('--output',required=True)
    v=sub.add_parser('validate');v.add_argument('result');v.add_argument('--schema')
    e=sub.add_parser('evaluate');e.add_argument('--result',required=True);e.add_argument('--truth',required=True);e.add_argument('--mapping',required=True,help='JSON reference-room to prediction-room map');e.add_argument('--output',required=True)
    t=sub.add_parser('repeat');t.add_argument('--first',required=True);t.add_argument('--second',required=True);t.add_argument('--output',required=True)
    args=p.parse_args()
    import cv2,numpy as np
    cv2.setRNGSeed(0);np.random.seed(0)
    try:
        if args.action=='run':
            if args.max_frames<2 or args.semantic_views<0:p.error('max-frames must be >=2, semantic-views >=0')
            from .pipeline import run
            run(args)
        elif args.action=='audit':
            from .io import load_scan
            scan=load_scan(args.input);write_json(args.output,scan['qa']);print(args.output)
        elif args.action=='validate':
            from .schema import validate
            validate(json.loads(Path(args.result).read_text()),args.schema);print('Schema and measurement invariants valid')
        elif args.action=='evaluate':
            from .evaluate import read_measurements,score,export_scores
            result=json.loads(Path(args.result).read_text());mapping=json.loads(args.mapping)
            export_scores([score(result,read_measurements(args.truth),mapping)],args.output);print(args.output)
        elif args.action=='repeat':
            from .evaluate import repeatability
            write_json(args.output,repeatability(json.loads(Path(args.first).read_text()),json.loads(Path(args.second).read_text())))
    except Exception as error:
        if args.action=='run':write_json(Path(args.output)/'run_status.json',{'status':'failed','error_type':type(error).__name__,'error':str(error)})
        raise
if __name__=='__main__':main()
