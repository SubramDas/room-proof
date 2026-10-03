"""Execute declared runs, keeping terminal logs and never hiding a failed run."""
import argparse,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from astra.runtime import install_progress_log
p=argparse.ArgumentParser();p.add_argument('--config',default='configs/benchmark.json');p.add_argument('--only',nargs='*');p.add_argument('--output-root',default='runs');p.add_argument('--skip-complete',action='store_true');args=p.parse_args()
config=json.loads((ROOT/args.config).read_text());out=ROOT/args.output_root;out.mkdir(parents=True,exist_ok=True);summary=[]
import hashlib
run_key=hashlib.sha256(json.dumps(args.only).encode()).hexdigest()[:10]
install_progress_log(out/'execution_logs'/f'{run_key}.log')
for run in config['runs']:
    name=run['id']
    if args.only and name not in args.only:continue
    target=out/name;status=target/'run_status.json'
    if args.skip_complete and status.exists() and json.loads(status.read_text()).get('status')=='complete_with_limitations':
        summary.append({'run':name,'status':'existing_output_not_rerun'});continue
    target.mkdir(parents=True,exist_ok=True);cmd=[sys.executable,'-m','astra','run','--output',str(target),'--capture-id',name]
    for key,val in run.items():
        if key=='id':continue
        if isinstance(val,bool):
            if val:cmd.append('--'+key.replace('_','-'))
        else:cmd+=['--'+key.replace('_','-'),str(val)]
    print('Running',name,flush=True);start=time.perf_counter()
    with (target/'terminal.log').open('w') as log:
        proc=subprocess.Popen(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        for line in proc.stdout:print(line,end='',flush=True);log.write(line);log.flush()
        code=proc.wait()
    summary.append({'run':name,'exit_code':code,'runtime_seconds':time.perf_counter()-start,'command':cmd})
    (out/f'execution_summary_{run_key}.json').write_text(json.dumps(summary,indent=2)+'\n')
if any(s.get('exit_code',0) for s in summary):sys.exit(1)
