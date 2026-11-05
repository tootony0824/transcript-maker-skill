# 本地识别

适用 Apple Silicon macOS，依赖 Python 和 ffmpeg。建议为本项目建立隔离环境，模型首次运行时按相应项目说明下载。模型可用本地路径替换，避免重复下载；安装和模型下载不应修改全局 Python 环境。

## 默认：Qwen3-ASR

[mlx-qwen3-asr](https://github.com/moona3k/mlx-qwen3-asr) 是社区 MLX 实现，支持 Qwen3-ASR 0.6B。JSON 中的 `chunks` 带识别文本及大致起止时间，不需要另行运行词级对齐：

```bash
python3 -m venv .venv
.venv/bin/pip install 'mlx-qwen3-asr==0.4.4'
.venv/bin/mlx-qwen3-asr /path/to/audio.m4a \
  --model Qwen/Qwen3-ASR-0.6B --language Chinese \
  --output-format json --output-dir /path/to/output
```

需要词级时间戳时添加 `--timestamps`，另需 Qwen3-ForcedAligner 模型；为避免下载，使用 `--forced-aligner /path/to/model` 指定本地模型。检查零时长、不递增和越界片段。模型长文件处理和截断情况须逐任务检查。某些噪声与音乐可能导致识别幻觉。

## 备用：MLX Whisper

```bash
python3 -m venv .venv-whisper
.venv-whisper/bin/pip install 'mlx-whisper==0.4.3'
.venv-whisper/bin/mlx_whisper /path/to/audio.m4a \
  --model mlx-community/whisper-large-v3-turbo --language zh \
  --output-format json --output-dir /path/to/output
```

`--word-timestamps True` 可选；默认 segment 级足以粗定位。保留各模型原始 JSON。运行环境、模型版本、音频和时间戳设置均会影响速度和质量。

## 生成正文草稿

`scripts/render_transcript.py` 支持 Qwen JSON 的 `chunks` 和 Whisper JSON 的 `segments`，检查时间范围并生成 Markdown 草稿。例：

```bash
python3 transcript-maker/scripts/render_transcript.py /path/to/result.json \
  --title '课程标题' --duration 3600 --output /path/to/draft.md
```

草稿中的时间是纯文本；媒体链接、来源、机器初审及异常核对需按任务补全，不能把草稿当作已经审校的成品。
