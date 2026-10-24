#!/usr/bin/env python3
"""Separate comparison outcomes from original capability/host execution failures."""
import json,re
from pathlib import Path
from collections import Counter
from verify_F53 import ROOT,PLUGINS
E=ROOT/'orchestra/reports/F53-evidence'
result={}
for plugin in PLUGINS:
 counts=Counter();original=Counter();mac_only=0;tags=Counter();first=None;cropped=0
 with (E/('survey-auto-'+plugin+'.jsonl')).open() as f:
  for line in f:
   row=json.loads(line);r=row['result'];o=r['oracle'];v=next(iter(r['routes'].values()))
   counts[dict(exact='E',mismatch='M',refusal='R').get(v['status'],'U')]+=1
   if v['status']=='mismatch' and first is None:first=dict(index=row['index'],diff=v.get('diff'),geometry_diff=v.get('geometry_diff'))
   for trace in row['refusals'].values():tags.update(trace)
   if v['status']=='refusal' and o['status']=='ok':mac_only+=1
   text=o.get('diagnostic','')
   if o['status']!='ok':
    if o['status']=='budget':kind='oracle_budget'
    elif 'did not advertise support' in text:kind='original_advertised_depth_unsupported'
    elif '_CxxThrowException' in text:kind='original_exception_host_cannot_unwind'
    elif 'UC_ERR_' in text:kind='oracle_execution_fault'
    elif re.search(r'(SMART_RENDER|RENDER) returned [1-9]',text):kind='original_plugin_PF_Err'
    else:kind='other_oracle_failure'
    original[kind]+=1
   for text in row['oracle_stderr']:
    m=re.search(r'F53_CHECKOUT request=\[[^\]]+\] result=(\[[^\]]+\]) max=(\[[^\]]+\])',text)
    if m and json.loads(m[1])!=json.loads(m[2]):cropped+=1;break
 assert sum(counts.values())==100
 result[plugin]=dict(EMRU={k:counts[k] for k in 'EMRU'},mac_only_refusals=mac_only,original_non_success=dict(original),refusal_tags=dict(tags),first_mismatch=first,original_cropped_checkouts=cropped)
(E/'classification.json').write_text(json.dumps(result,indent=2)+'\n')
for k,v in result.items():print(k,*v['EMRU'].values(),'Mac-only R',v['mac_only_refusals'],'original',v['original_non_success'])
