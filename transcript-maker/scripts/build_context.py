#!/usr/bin/env python3
"""Build an ASR context from explicitly selected vocabulary groups."""
import argparse
import json
from pathlib import Path


def build_context(groups, selected, max_terms=30):
    if not selected:
        raise ValueError('select at least one vocabulary group')
    terms, seen = [], set()
    for group in selected:
        if group not in groups or not isinstance(groups[group], list):
            raise ValueError(f'unknown or invalid group: {group}')
        for term in groups[group]:
            if not isinstance(term, str) or not term.strip() or '\n' in term or '\r' in term:
                raise ValueError('terms must be nonempty single-line strings')
            term = term.strip()
            if term.casefold() not in seen:
                terms.append(term)
                seen.add(term.casefold())
    if len(terms) > max_terms:
        raise ValueError(f'too many terms ({len(terms)}); select fewer relevant groups')
    return ' '.join(terms)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vocabulary', type=Path, default=Path(__file__).resolve().parents[1] / 'assets/vocabulary.json')
    parser.add_argument('--group', action='append', required=True)
    args = parser.parse_args()
    try:
        print(build_context(json.loads(args.vocabulary.read_text(encoding='utf-8')), args.group))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
