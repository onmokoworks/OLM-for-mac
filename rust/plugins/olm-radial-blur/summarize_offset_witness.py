"""Collect all predeclared integration-witness rerenders, never select lucky runs."""
import ast, hashlib, json, re
from pathlib import Path

OWN=Path(__file__).resolve().parent
ROOT=OWN.parents[2]
def identity(p):
    p=Path(p).resolve()
    return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

if __name__=='__main__':
    history=json.loads((ROOT/'rust/evidence/integration/radial-triage.json').read_text())
    old=next(r for r in history['results'] if r['route']=='smart32')
    replay=json.loads((OWN/'validation/integration-offset-replays/summary.json').read_text())['results'][0]
    controls=json.loads((OWN/'validation/integration-offset-controls/summary.json').read_text())
    log=OWN/'validation/integration-offset-tests-confirmed.log'
    text=log.read_text(); assert '8 passed; 0 failed; 1 ignored' in text
    line=next(s for s in text.splitlines() if s.startswith('phase_bits='))
    cells=ast.literal_eval(re.search(r'underread_cells=(.*?);',line)[1])
    support=ast.literal_eval(re.search(r'underread_sensitive_output_pixels=(.*?);',line)[1])
    mismatch=ast.literal_eval(re.search(r'observed_mismatch_pixels=(.*)$',line)[1])
    assert len(replay['replays'])==10 and replay['all_replays_succeeded'] and replay['candidate_unique']==1
    assert old['replay_candidate']==replay['replay_candidate']
    assert len(set(old['candidate_output_hashes']+replay['candidate_output_hashes']))==1
    assert all(r['status']=='exact' for r in controls['results']) and len(controls['results'])==2
    assert set(mismatch)<=set(support)
    for side in ['reference','candidate','harness']:
        assert identity(controls['identities'][side]['path'])==controls['identities'][side]
    replays=[{'number':i+1,'reference_sha256':replay['reference_output_hashes'][i+1],
              'candidate_sha256':replay['candidate_output_hashes'][i+1],
              'status':r['status'],'comparison':r['comparison'],'processes':r['processes']}
             for i,r in enumerate(replay['replays'])]
    evidence={'same_input_params_route_except_slot28':True,'zero_offset_exact':True,
              'positive_offset_exact':True,'cpp_zero_read_equivalent':True,
              'mismatches_within_underread_support':True,
              'controls_summary':identity(OWN/'validation/integration-offset-controls/summary.json'),
              'localization_test_log':identity(log)}
    replay['offset_control_evidence']=evidence
    report={'classification':'excluded_original_nondeterminism','baseline_status':'mismatched',
            'counts_added_to_campaign':0,'predeclared_additional_replays':10,
            'identities':controls['identities'], 'historical_original_hashes':old['reference_output_hashes'],
            'witness_case':identity(Path(old['source'])/'case.json'),
            'input_png':identity(Path(old['source'])/'input.png'),
            'expected_native_float_output':identity(Path(old['source'])/'candidate.rgba32f-le'),
            'historical_triage':identity(ROOT/'rust/evidence/integration/radial-triage.json'),
            'all_14_candidate_unique':1,
            'all_14_original_unique':len(set(old['reference_output_hashes']+replay['reference_output_hashes'])),
            'additional_exact':sum(r['status']=='exact' for r in replays),'additional_replays':replays,
            'controls':controls['results'],'offset_control_evidence':evidence,
            'noise_lattice_size':[15,31],'phase_bits':'c0b1cf36','underread_cells_and_endpoint_indices':cells,
            'cpp_exact_phases_degrees':[-318.36653167426726,0,1],
            'underread_counterfactual_values':[-1,1],'underread_sensitive_pixel_indices':support,
            'underread_sensitive_source_pixel_indices':ast.literal_eval(re.search(r'underread_sensitive_source_pixels=(.*)',text)[1]),
            'observed_mismatch_pixel_indices':mismatch,
            'evidence_boundary':'Sensitivity is measured in the pure Rust Smart32 renderer matching the staged DLL; original under-read cause is source-grounded inference, not a native memory trace.',
            'production_algorithm_changed':False,'full_campaign_rerun':False,
            'source_files':[identity(p) for p in [OWN/'src/noise.rs',OWN/'tests/support/offset_witness.rs',OWN/'tests/support/offset_witness_data.rs',ROOT/'core/dblur_noise.h']],
            'test_log':identity(log)}
    (OWN/'offset-witness.json').write_text(json.dumps(report,indent=2))
    (OWN/'validation/integration-offset-adjudication.json').write_text(json.dumps({'complete':True,'results':[replay]},indent=2))
    print('original unique across 14:',report['all_14_original_unique'],'additional exact:',report['additional_exact'])
