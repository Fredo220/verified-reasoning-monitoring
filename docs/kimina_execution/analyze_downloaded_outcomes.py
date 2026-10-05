"""Read-only receipt analysis; no model inference or changes to source data."""
from pathlib import Path
from collections import Counter
import hashlib, json, re

roots=[Path('/Users/friedrichreichelt/Downloads/results'),Path('/Users/friedrichreichelt/Downloads/results 2')]
files={p.name:p for root in roots for p in root.iterdir() if p.is_file() and p.suffix=='.json'}
def load(name):
    return json.loads(files[name].read_text())
def payload(name):
    e=load(name)
    expected=hashlib.sha256(json.dumps(e['payload'],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    assert expected==e['payload_sha256'],name
    return e['payload']
request=load('request.json'); rows=[]
for a in request['attempts']:
    key=f"{a['task_id']}-{a['index']:03d}"
    r=payload(key+'.json'); c=r['candidate']; text=c['text']
    words=re.findall(r'\S+',text)
    grams=Counter(tuple(words[i:i+12]) for i in range(max(0,len(words)-11)))
    lines=[line.strip() for line in text.splitlines() if len(line.strip())>=40]
    repeated=Counter(lines)
    rows.append({'key':key,'finish':c['finish_reason'],'think_open':text.count('<think>'),'think_close':text.count('</think>'),
                 'generation_s':c['generation_s'],'capture_s':c['extraction_s'],'elapsed_s':c['elapsed_s'],
                 'storage_s':r['storage_s'],'deadline_exceeded':c['deadline_exceeded'],
                 'remaining_at_start_s':payload('started-'+key+'.json')['remaining_s'],
                 'tokens':len(c['output_ids']),'word_12gram_duplicate_fraction':1-len(grams)/sum(grams.values()),
                 'frequent_long_lines':repeated.most_common(3), 'head':text[:900],'tail':text[-900:]})
summary=payload('summary.json')
backups=[(n,payload(n)) for n in sorted(files) if n.startswith('backup-cost-')]
load_s=sum(payload(n)['elapsed_s'] for n in files if n.startswith('load-'))
backup_s=sum(p['elapsed_s'] for _,p in backups)
base=request['prior_gpu_s']+load_s+sum(r['elapsed_s']+r['storage_s'] for r in rows)
assert abs(base+sum(p['elapsed_s'] for _,p in backups[:-1])-summary['measured_gpu_pipeline_s'])<0.05
wrapper=load(next(n for n in files if n.startswith('wrapper-')))
report={'scope':'descriptive-two-task-analysis-not-H1-H3','rows':rows,'costs':{
    'prior_s':request['prior_gpu_s'],'model_load_s':load_s,
    'generation_s':sum(r['generation_s'] for r in rows),'capture_s':sum(r['capture_s'] for r in rows),
    'storage_s':sum(r['storage_s'] for r in rows),'backup_s':backup_s,
    'recorded_summary_cumulative_s':summary['measured_gpu_pipeline_s'],
    'reconstructed_cumulative_including_last_backup_s':base+backup_s,
    'last_backup_missing_from_summary_s':backups[-1][1]['elapsed_s'],
    'allowance_s':3600,'overrun_including_last_backup_s':base+backup_s-3600,
    'wrapper_s_excluding_final_export':wrapper['wall_s'],
    'wrapper_minus_new_pipeline_s':wrapper['wall_s']-(base+backup_s-request['prior_gpu_s']),
    'final_export_and_remount_receipt_present':any(n.startswith('persistence-') for n in files)},
    'backup_records':len(backups),'model_repair_eligible_under_current_policy':0,
    'limits':['No Lean validity labels produced','No causal diagnosis from generated reasoning text','No full numerical activation revalidation']}
Path('/private/tmp/kimina-outcome-analysis.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
