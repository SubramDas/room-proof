"""Score supplied physical correspondence, without inventing an app baseline."""
import argparse,csv,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('csv');p.add_argument('--output',required=True);args=p.parse_args()
rows=list(csv.DictReader(open(args.csv)));out=[]
for r in rows:
    truth=float(r['truth_m']);a=float(r['pipeline_m']) if r.get('pipeline_m') else None;b=float(r['app_m']) if r.get('app_m') else None
    ae=abs(a-truth) if a is not None else None;be=abs(b-truth) if b is not None else None
    out.append({**r,'pipeline_error_m':ae,'app_error_m':be,'beat_or_tie':ae is not None and be is not None and ae<=be+1e-9})
rate=sum(r['beat_or_tie'] for r in out)/len(out) if out else None
result={'rows':out,'beat_or_tie_fraction_all_submitted_dimensions':rate,'gate':.70,'pass':rate>=.70 if rate is not None else None,'status':'scored' if out else 'missing_exports'}
Path(args.output).parent.mkdir(parents=True,exist_ok=True);Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
