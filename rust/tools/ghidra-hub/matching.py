"""Conservative one-to-one function matching, independent of Java for testing."""
from collections import defaultdict


def match_functions(source, target, same_hash=False):
    matches, used = {}, set()
    if same_hash:
        by_rva = {r['rva']: r for r in target}
        for row in source:
            if row['rva'] in by_rva:
                other = by_rva[row['rva']]
                matches[row['address']] = dict(target=other['address'], method='binary-sha256+rva')
                used.add(other['address'])
    else:
        for field in ['raw_hash', 'normalized_hash']:
            left, right = defaultdict(list), defaultdict(list)
            for row in source:
                if row.get(field) and row['address'] not in matches and row['instructions'] >= 5:
                    left[row[field]].append(row)
            for row in target:
                if row.get(field) and row['address'] not in used and row['instructions'] >= 5:
                    right[row[field]].append(row)
            for value, rows in left.items():
                candidates = right[value]
                if len(rows) == len(candidates) == 1:
                    a, b = rows[0], candidates[0]
                    matches[a['address']] = dict(target=b['address'], method=field)
                    used.add(b['address'])
    return dict(matches=matches, unmatched=[r['address'] for r in source if r['address'] not in matches],
                new=[r['address'] for r in target if r['address'] not in used])
