#!/usr/bin/env python3
"""Test two rectangle-only DirectionalBlur fixes in scratch source copies."""
import importlib
from pathlib import Path
import re
import shutil
import time
from core import evaluate, load_corpus, sha
from qualify_T15 import S, E, adapter, write


def main():
    module=importlib.import_module('adapters.olmdirectionalblur')
    original_path=module.SOURCE
    original=original_path.read_text()
    replacements={
        'forward-request': ('req.rect = PF_LRect{0, 0, full_width, full_height};',
                            '// Experiment: retain the incoming ROI request.'),
        'advertise-request': ('UnionLRect(&in_result.result_rect, &extra->output->result_rect);',
                              'UnionLRect(&extra->input->output_request.rect, &extra->output->result_rect);'),
    }
    results=[]
    for name,(old,new) in replacements.items():
        assert original.count(old)==1
        directory=S/('experiment-'+name)
        directory.mkdir(parents=True,exist_ok=True)
        source_dir=directory/'sources/mac/OLMDirectionalBlur';source_dir.mkdir(parents=True,exist_ok=True)
        changed=original.replace(old,new)
        # Relative quoted includes retain their original meaning in the copy.
        changed=re.sub(r'#include "([^"\n]+)"',lambda m:'#include "'+str((original_path.parent/m[1]).resolve())+'"',changed)
        source=source_dir/original_path.name;source.write_text(changed)
        for suffix in ('OLMDirectionalBlur.h','OLMDirectionalBlur_Strings.cpp','OLMDirectionalBlur_Strings.h'):
            (source_dir/suffix).symlink_to(original_path.with_name(suffix))
        module.SOURCE=source
        try:
            a=adapter('olmdirectionalblur',directory)
            a.routes=('smart',);a.oracle_routes={'smart':'smart'}
            deadline=time.monotonic()+300
            provenance=a.prepare(directory,deadline)
            case,_=load_corpus(Path('tests/fuzz_corpus/olmdirectionalblur/T15-prerequisite-realistic/rectangle.json'),a)
            attr={};result=evaluate(a,case,directory,deadline,attr)
            results.append(dict(hypothesis=name,replace_from=old,replace_to=new,
                                baseline_source_sha256=sha(original.encode()),
                                experiment_source_sha256=sha(changed.encode()),
                                case={k:v for k,v in case.items() if k!='pixels'},
                                result=result,refusals=attr,provenance=provenance))
            print(name,result['routes']['smart']['status'],attr,flush=True)
        finally:
            module.SOURCE=original_path
            shutil.rmtree(directory)
    write(E/'local-fix-experiments.json',results)

if __name__=='__main__':main()
