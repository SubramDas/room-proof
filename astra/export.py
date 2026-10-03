from pathlib import Path
import html,json
import numpy as np
from .io import write_json


def render(result,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots(figsize=(11,8));colors=plt.get_cmap('Set3')
    for i,room in enumerate(result['rooms']):
        p=np.array(room['polygon']);ax.add_patch(Polygon(p,facecolor=colors(i%12),edgecolor='#243047',linewidth=2,alpha=.65))
        center=p.mean(0);h=room['ceiling_height']['value'];area=room['floor_area']['value']
        text=f"{room['name']}\n{area:.2f} m²\nh={h:.2f} m" if h else f"{room['name']}\n{area:.2f} m²\nheight unobserved"
        ax.text(*center,text,ha='center',va='center',fontsize=9)
        for wall in room['walls']:
            a=np.array(wall['start']);b=np.array(wall['end']);m=(a+b)/2;length=wall['length']['value']
            if length>.35:ax.text(*m,f'{length:.2f}',fontsize=7,ha='center',bbox=dict(facecolor='white',alpha=.75,edgecolor='none',pad=1))
    surfaces={s['id']:s for s in result['surfaces']}
    for op in result['openings']:
        s=surfaces[op['surface_id']];a=np.array(s['start']);b=np.array(s['end']);e=(b-a)/np.linalg.norm(b-a);low,high=np.array(op['surface_uv_bounds']);ends=np.array([a+e*low[0],a+e*high[0]])
        ax.plot(ends[:,0],ends[:,1],color='#e27413',linewidth=4,linestyle='--');mid=ends.mean(0);ax.text(*mid,f"{op['width']['value']:.2f} m ?",fontsize=7,color='#913300')
    ax.autoscale();ax.set_aspect('equal');ax.set_xlabel('Property x (m)');ax.set_ylabel('Property z (m)');ax.grid(alpha=.2)
    ax.set_title(f"Astra — {result['tier']} — {result['capture_id']}\n{result['status']}",fontsize=12)
    fig.text(.02,.015,'Dimensions in metres. Orange: unverified openings. Intervals and evidence in result.json/report.html.\nProvisional uncertainty; no accuracy-gate claim. Disconnected RGB components are schematic placements.',fontsize=8)
    fig.tight_layout(rect=[0,.05,1,1]);fig.savefig(out/'plan.svg');fig.savefig(out/'plan.pdf');fig.savefig(out/'plan.png',dpi=150);plt.close(fig)
    rows=[]
    for room in result['rooms']:
        for name in ['ceiling_height','floor_area','extent_x','extent_z']:
            m=room[name];interval=m['interval'];rows.append(f"<tr><td>{html.escape(room['id'])}</td><td>{name}</td><td>{m['value']}</td><td>{m['unit']}</td><td>{interval['lower']} – {interval['upper']}</td><td>{interval['calibration_status']}</td></tr>")
    for room in result['rooms']:
        for wall in room['walls']:
            m=wall['length'];iv=m['interval'];rows.append(f"<tr><td>{html.escape(wall['surface_id'])}</td><td>wall length</td><td>{m['value']:.3f}</td><td>m</td><td>{iv['lower']:.3f} – {iv['upper']:.3f}</td><td>{iv['calibration_status']}</td></tr>")
    for op in result['openings']:
        for key in ['width','height']:
            m=op[key];iv=m['interval'];rows.append(f"<tr><td>{html.escape(op['id'])}</td><td>opening {key}</td><td>{m['value']:.3f}</td><td>m</td><td>{iv['lower']:.3f} – {iv['upper']:.3f}</td><td>{iv['calibration_status']}</td></tr>")
    damage_rows=''.join(f"<tr><td>{html.escape(d['id'])}</td><td><a href='surfaces/{html.escape(d['surface_id'])}.svg'>{html.escape(d['surface_id'])}</a></td><td>{html.escape(d['class'])}</td><td>{d['area']['value']:.3f} m²</td><td>{html.escape(d['status'])}</td></tr>" for d in result['damage'])
    flags=''.join(f"<li>{html.escape(f['rule'])}: {html.escape(f['message'])}</li>" for f in result['concealed_damage_flags'])
    scope=''.join(f"<li>{html.escape(s['surface_id'])}: {html.escape(s['action'])} ({s['quantity']['value']:.3f} {s['quantity']['unit']}); rule {html.escape(s['rule'])}</li>" for s in result['scope_items'])
    warnings=''.join(f'<li>{html.escape(w)}</li>' for w in result['warnings'])
    (out/'report.html').write_text('<!doctype html><html><meta charset="utf-8"><title>Astra capture report</title><style>body{font:16px system-ui;margin:32px;max-width:1200px}img{max-width:100%}table{border-collapse:collapse;font-size:13px}td,th{padding:8px;border:1px solid #ddd}code{background:#eee}</style>'
        +f"<h1>{html.escape(result['capture_id'])}</h1><p>{html.escape(result['status'])}</p><img src='plan.svg' alt='Property floor plan'><h2>Limitations</h2><ul>{warnings}</ul>"
        +'<h2>Measurement intervals</h2><p>Engineering uncertainty ranges are provisional until independently calibrated.</p><table><tr><th>Room</th><th>Measurement</th><th>Value</th><th>Unit</th><th>95% nominal range</th><th>Calibration</th></tr>'+''.join(rows)+'</table>'
        +f"<h2>Damage candidates</h2><table><tr><th>Region</th><th>Surface</th><th>Class</th><th>Observed area</th><th>Status</th></tr>{damage_rows}</table><h2>Inspection flags</h2><ul>{flags}</ul><p>An empty list is not evidence of no concealed damage.</p><h2>Scope items</h2><ul>{scope}</ul>"
        +f"<h2>Evidence</h2><p>{len(result['openings'])} opening candidates; {len(result['damage'])} damage regions; {len(result['scope_items'])} scope items.</p><p><a href='result.json'>Full JSON</a> · <a href='provenance.json'>Provenance</a> · <a href='semantics/candidates.json'>Visual candidates</a></p></html>")
    (out/'rooms').mkdir(exist_ok=True);(out/'surfaces').mkdir(exist_ok=True)
    for room in result['rooms']:
        f,a=plt.subplots(figsize=(6,6));p=np.array(room['polygon']);a.add_patch(Polygon(p,fill=False));a.autoscale();a.axis('equal');a.set_title(f"{room['id']} — {room['floor_area']['value']:.2f} m²");a.set_xlabel('x (m)');a.set_ylabel('z (m)')
        for wall in room['walls']:
            mid=(np.array(wall['start'])+wall['end'])/2;a.text(*mid,f"{wall['length']['value']:.2f} m",ha='center',fontsize=9,bbox={'facecolor':'white','edgecolor':'none','alpha':.8})
        f.tight_layout();f.savefig(out/'rooms'/f"{room['id']}.svg");plt.close(f)
    for s in result['surfaces']:
        if s['kind']!='wall':continue
        f,a=plt.subplots(figsize=(7,4));length=np.linalg.norm(np.array(s['end'])-s['start']);height=s['height']['value'] or 3
        a.set_xlim(0,length);a.set_ylim(0,height);a.set_aspect('equal');a.set_title(s['id']);a.set_xlabel('Along wall (m)');a.set_ylabel('Height above floor (m)')
        for d in result['damage']:
            if d['surface_id']==s['id']:a.add_patch(Polygon(d['surface_polygon'],alpha=.5,facecolor='orange'));a.text(*np.mean(d['surface_polygon'],axis=0),d['class'],fontsize=7)
        f.savefig(out/'surfaces'/f"{s['id']}.svg");plt.close(f)
