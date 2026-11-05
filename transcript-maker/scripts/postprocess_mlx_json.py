#!/usr/bin/env python3
"""Restore punctuation in MLX Whisper JSON without changing recognized text."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import sherpa_onnx


PUNCTUATION = frozenset("，。！？、；：,.?!;:…")
SENTENCE_END = frozenset("。！？?!")
DEFAULT_MODEL = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12"
    / "model.onnx"
)


@dataclass
class Atom:
    char: str
    start: float
    end: float
    word_id: int
    punctuation: str = ""


@dataclass
class SegmentAtoms:
    start: float
    end: float
    original_text: str
    atoms: list[Atom]


def normalized_characters(text: str) -> str:
    return "".join(
        char.casefold()
        for char in text
        if not char.isspace() and char not in PUNCTUATION
    )


def make_atoms(segment: dict[str, Any], first_word_id: int) -> tuple[list[Atom], int]:
    segment_text = str(segment.get("text", ""))
    segment_start = float(segment["start"])
    segment_end = float(segment["end"])
    words = segment.get("words") or []
    word_text = "".join(str(word.get("word", "")) for word in words)
    use_words = bool(words) and normalized_characters(word_text) == normalized_characters(segment_text)

    atoms: list[Atom] = []
    if use_words:
        for offset, word in enumerate(words):
            word_id = first_word_id + offset
            start = float(word.get("start", segment_start))
            end = float(word.get("end", segment_end))
            for char in str(word.get("word", "")):
                if char in PUNCTUATION:
                    if atoms:
                        atoms[-1].punctuation += char
                elif not char.isspace():
                    atoms.append(Atom(char=char, start=start, end=end, word_id=word_id))
        return atoms, first_word_id + len(words)

    word_id = first_word_id
    for char in segment_text:
        if char in PUNCTUATION:
            if atoms:
                atoms[-1].punctuation += char
        elif not char.isspace():
            atoms.append(
                Atom(char=char, start=segment_start, end=segment_end, word_id=word_id)
            )
            word_id += 1
    return atoms, word_id


def is_ascii_word_char(char: str) -> bool:
    return char.isascii() and (char.isalnum() or char in "_-'" )


def render_atoms(atoms: list[Atom], include_punctuation: bool = True) -> str:
    parts: list[str] = []
    previous: Atom | None = None
    for atom in atoms:
        if (
            previous is not None
            and atom.word_id != previous.word_id
            and is_ascii_word_char(previous.char)
            and is_ascii_word_char(atom.char)
        ):
            parts.append(" ")
        parts.append(atom.char)
        if include_punctuation and atom.punctuation:
            parts.append(atom.punctuation)
        previous = atom
    return "".join(parts)


def load_segments(
    input_path: Path, start_time: float | None, end_time: float | None
) -> tuple[dict[str, Any], list[SegmentAtoms]]:
    source = json.loads(input_path.read_text(encoding="utf-8"))
    raw_segments = source.get("segments")
    if not isinstance(raw_segments, list):
        raise ValueError("输入 JSON 缺少 MLX Whisper 的 segments 数组")

    result: list[SegmentAtoms] = []
    word_id = 0
    for segment in raw_segments:
        start = float(segment.get("start", 0))
        end = float(segment.get("end", 0))
        if end <= start or not str(segment.get("text", "")).strip():
            continue
        if start_time is not None and end <= start_time:
            continue
        if end_time is not None and start >= end_time:
            continue
        atoms, word_id = make_atoms(segment, word_id)
        if atoms:
            result.append(
                SegmentAtoms(
                    start=start,
                    end=end,
                    original_text=str(segment["text"]),
                    atoms=atoms,
                )
            )
    if not result:
        raise ValueError("指定时间范围内没有可处理的文字")
    return source, result


def make_chunks(segments: list[SegmentAtoms], max_chars: int) -> list[list[Atom]]:
    chunks: list[list[Atom]] = []
    current: list[Atom] = []
    previous_end: float | None = None
    previous_had_sentence_end = False
    for segment in segments:
        gap = 0 if previous_end is None else max(0, segment.start - previous_end)
        should_flush = bool(current) and (
            len(current) + len(segment.atoms) > max_chars
            or (gap >= 1.2 and len(current) >= 60)
            or (previous_had_sentence_end and len(current) >= 60)
        )
        if should_flush:
            chunks.append(current)
            current = []
        current.extend(segment.atoms)
        previous_end = segment.end
        previous_had_sentence_end = segment.original_text.rstrip().endswith(
            tuple(SENTENCE_END)
        )
    if current:
        chunks.append(current)
    return chunks


def apply_model(model: Any, atoms: list[Atom]) -> str | None:
    model_input = render_atoms(atoms, include_punctuation=False)
    restored = model.add_punctuation(model_input)
    if normalized_characters(model_input) != normalized_characters(restored):
        return "模型输出改变了正文字符"

    cursor = 0
    predicted_punctuation = [""] * len(atoms)
    for char in restored:
        if char.isspace():
            continue
        if char in PUNCTUATION:
            if cursor > 0:
                predicted_punctuation[cursor - 1] += char
            continue
        if cursor >= len(atoms) or atoms[cursor].char.casefold() != char.casefold():
            return "模型输出无法映射回原始时间戳"
        cursor += 1
    if cursor != len(atoms):
        return "模型输出的时间戳映射不完整"
    for atom, punctuation in zip(atoms, predicted_punctuation):
        atom.punctuation = punctuation
    return None


def split_sentences(atoms: list[Atom]) -> list[dict[str, Any]]:
    sentences: list[dict[str, Any]] = []
    current: list[Atom] = []
    for atom in atoms:
        current.append(atom)
        if any(mark in SENTENCE_END for mark in atom.punctuation):
            sentences.append(sentence_record(current))
            current = []
    if current:
        sentences.append(sentence_record(current))
    return sentences


def sentence_record(atoms: list[Atom]) -> dict[str, Any]:
    return {
        "start": atoms[0].start,
        "end": atoms[-1].end,
        "text": render_atoms(atoms),
    }


def make_paragraphs(
    sentences: list[dict[str, Any]], target_seconds: float, target_chars: int
) -> list[dict[str, Any]]:
    paragraphs: list[dict[str, Any]] = []
    for sentence in sentences:
        current = paragraphs[-1] if paragraphs else None
        should_start = current is None or (
            sentence["end"] - current["start"] > target_seconds
            or len(current["text"]) + len(sentence["text"]) > target_chars
        )
        if should_start:
            paragraphs.append(dict(sentence))
        else:
            current["end"] = sentence["end"]
            current["text"] += sentence["text"]
    return paragraphs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="为 MLX Whisper JSON 恢复标点并映射原始时间戳"
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--start-time", type=float)
    parser.add_argument("--end-time", type=float)
    parser.add_argument("--num-threads", type=int, default=2)
    parser.add_argument("--max-model-chars", type=int, default=180)
    parser.add_argument("--paragraph-seconds", type=float, default=30)
    parser.add_argument("--paragraph-chars", type=int, default=240)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.model.is_file():
        raise FileNotFoundError(f"找不到标点模型：{args.model}")

    source, segment_groups = load_segments(args.input, args.start_time, args.end_time)
    chunks = make_chunks(segment_groups, args.max_model_chars)
    config = sherpa_onnx.OfflinePunctuationConfig(
        model=sherpa_onnx.OfflinePunctuationModelConfig(
            ct_transformer=str(args.model),
            num_threads=args.num_threads,
            debug=False,
            provider="cpu",
        )
    )
    model = sherpa_onnx.OfflinePunctuation(config)
    fallback_chunks: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks, start=1):
        fallback_reason = apply_model(model, chunk)
        if fallback_reason is not None:
            fallback_chunks.append(
                {
                    "chunk": index,
                    "start": chunk[0].start,
                    "end": chunk[-1].end,
                    "reason": fallback_reason,
                    "action": "保留 MLX 原生标点",
                }
            )

    all_atoms = [atom for group in segment_groups for atom in group.atoms]
    sentences = split_sentences(all_atoms)
    paragraphs = make_paragraphs(
        sentences, args.paragraph_seconds, args.paragraph_chars
    )
    output = {
        "metadata": {
            "engine": "sherpa-onnx",
            "engine_version": sherpa_onnx.__version__,
            "model": args.model.parent.name,
            "text_preserved": True,
            "source_language": source.get("language"),
            "source_path": str(args.input.resolve()),
            "start_time": args.start_time,
            "end_time": args.end_time,
            "chunks": len(chunks),
            "fallback_chunks": fallback_chunks,
        },
        "sentences": sentences,
        "paragraphs": paragraphs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "chunks": len(chunks),
                "sentences": len(sentences),
                "paragraphs": len(paragraphs),
                "text_preserved": True,
                "fallback_chunks": len(fallback_chunks),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
