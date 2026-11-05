#!/usr/bin/env python3
"""Render timestamped ASR JSON as a Markdown draft."""
import argparse
import json
import math
from pathlib import Path


def render(data, title, duration):
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('duration must be positive and finite')
    if data.get('truncated'):
        raise ValueError('transcription is truncated; inspect it before rendering')
    chunks = data.get('chunks') or data.get('segments') or []
    if not chunks:
        raise ValueError('no timestamped chunks or segments')
    lines = [f'# {title}', '', '> 机器识别草稿：尚未审校，时间戳为粗定位。', '', '## 逐字稿', '']
    previous = -1.0
    for chunk in chunks:
        if chunk.get('truncated'):
            raise ValueError('a chunk is truncated')
        start, end = float(chunk['start']), float(chunk['end'])
        if not all(math.isfinite(x) for x in (start, end)) or start < previous or start < 0 or end < start or end > duration + 0.1:
            raise ValueError('invalid timestamp range or ordering')
        previous = start
        text = str(chunk.get('text', '')).strip()
        if not text:
            continue
        seconds = int(start)
        stamp = f'{seconds // 3600:02}:{seconds // 60 % 60:02}:{seconds % 60:02}'
        lines += [f'[{stamp}] {text}', '']
    if len(lines) == 6:
        raise ValueError('no nonempty transcript text')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--title', required=True)
    parser.add_argument('--duration', required=True, type=float, help='media duration in seconds')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    content = render(json.loads(args.input.read_text(encoding='utf-8')), args.title, args.duration)
    args.output.write_text(content, encoding='utf-8')


if __name__ == '__main__':
    main()
