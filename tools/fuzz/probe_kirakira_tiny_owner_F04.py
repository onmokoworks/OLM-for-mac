#!/usr/bin/env python3
"""F04 scratch-only Smart owner geometry experiment; never relax production.

Arguments after --experiment/--sanitizers/--details are passed to run.py.
Owner geometry and rendering admission remain separate: owner alone retains the
9x7 tuple minimum. owner-tuples measures the outputs hidden by the tuple gates.
No arithmetic, helper fallback, Classic layout or ROI admission is changed.
"""
import argparse
import copy
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import run
from adapters import olmkirakira
from core import sha
from triage_kirakira import difference_details


def owner_source(source):
    start = source.index('static bool IsGenericBetaFullFrameDimensions(')
    end = source.index('\n}\n', start) + 3
    owner = source[start:end].replace('IsGenericBetaFullFrameDimensions',
                                     'IsSmartOwnerFullFrameDimensions')
    owner = owner[:owner.index('\n\t//')] + '''
\t// F04 experiment: storage geometry is independent of helper admission.
\tconstexpr int64_t kMaxGenericPixels = INT64_C(4096) * INT64_C(2160);
\treturn width >= 1 && height >= 1 && width <= 4096 && height <= 4096 &&
\t\tstatic_cast<int64_t>(width) * static_cast<int64_t>(height) <= kMaxGenericPixels;
}
'''
    source = source[:end] + '\n' + owner + source[end:]
    # Only the Smart dimension extractor, world/predata validation consume the
    # owner predicate. In particular, tuple/kernel admission stays unchanged.
    start = source.index('static bool GenericBetaRenderDimensions(')
    prefix, smart = source[:start], source[start:]
    assert smart.count('IsGenericBetaFullFrameDimensions(') == 3
    smart = smart.replace('IsGenericBetaFullFrameDimensions(',
                          'IsSmartOwnerFullFrameDimensions(')
    return prefix + smart


def main():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--experiment', choices=('baseline', 'request', 'owner', 'owner-tuples'), required=True)
    p.add_argument('--sanitizers', action='store_true')
    p.add_argument('--details', type=Path, required=True)
    args, rest = p.parse_known_args()
    records = []
    original = olmkirakira.Adapter

    class ExperimentAdapter(original):
        def compile(self, argv, deadline):
            argv = list(argv)
            if argv[0] == 'clang++':
                host = next(Path(x) for x in argv if str(x).endswith('/host.cpp'))
                source = olmkirakira.SOURCE.read_text()
                if args.experiment.startswith('owner'):
                    source = owner_source(source)
                if args.experiment == 'request':
                    old = 'if (!exact_request_matches_known_frame &&\n\t\t!request_contains_generic_full_frame) {'
                    assert source.count(old) == 1
                    source = source.replace(old, 'if (false) {')
                if args.experiment == 'owner-tuples':
                    old = 'if (!exact_closure && !generic_beta) {'
                    assert source.count(old) == 2
                    source = source.replace(old, 'if (false) {')
                source = source.replace('#include "OLMKiraKira.h"',
                    '#include "'+str(olmkirakira.SOURCE.with_suffix('.h'))+'"')
                source = source.replace('#include "../../core/',
                    '#include "'+str(olmkirakira.ROOT/'core')+'/')
                snapshot = host.parent/'tiny_owner.cpp'
                snapshot.write_text(source)
                host.write_text(host.read_text().replace(str(olmkirakira.SOURCE), str(snapshot)))
                if args.sanitizers:
                    argv[1:1] = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                                 '-fno-omit-frame-pointer', '-g']
                    self.env.update(ASAN_OPTIONS='detect_leaks=0',
                                    UBSAN_OPTIONS='print_stacktrace=1:halt_on_error=1')
                self.experiment_binding = dict(experiment=args.experiment,
                    sanitizers=args.sanitizers, scratch_source_sha256=sha(source.encode()),
                    production_source_sha256=sha(olmkirakira.SOURCE.read_bytes()))
            return super().compile(argv, deadline)

        def prepare(self, scratch, deadline):
            result = super().prepare(scratch, deadline)
            return dict(result, experiment=self.experiment_binding)

        def oracle(self, case, directory, deadline, route=None):
            status, raw = super().oracle(case, directory, deadline, route)
            reference = directory/f'reference-{route or self.oracle_route}.raw'
            reference.unlink(missing_ok=True)
            if status['status'] == 'ok':
                reference.write_bytes(raw)
            return status, raw

        def candidate(self, case, directory, route, deadline):
            traced = copy.copy(self)
            path = directory/(route+'.trace')
            path.unlink(missing_ok=True)
            traced.env = dict(self.env, OLMKIRAKIRA_DIAGNOSTIC_LOG=str(path))
            outcome = original.candidate(traced, case, directory, route, deadline)
            row = dict(index=case['index'], geometry=case['geometry'], depth=case['depth'],
                       route=route, input_sha256=sha(case['pixels']),
                       candidate=outcome[0], guards=outcome[2],
                       trace=path.read_text().splitlines() if path.exists() else [])
            reference = directory/f'reference-{route or self.oracle_route}.raw'
            if reference.exists() and outcome[0]['status'] == 'ok':
                expected = reference.read_bytes()
                row['exact'] = expected == outcome[1]
                if not row['exact']:
                    row['difference'] = difference_details(expected, outcome[1], case)
            records.append(row)
            return outcome

    olmkirakira.Adapter = ExperimentAdapter
    sys.argv = [sys.argv[0], *rest]
    code = run.main()
    args.details.parent.mkdir(parents=True, exist_ok=True)
    args.details.write_text(json.dumps(sorted(records, key=lambda r:(r['index'],r['route'])),
                                      indent=2, sort_keys=True)+'\n')
    return code


if __name__ == '__main__':
    sys.exit(main())
