# 逐字稿生成 Skill

面向 Codex 的本地逐字稿技能：从音视频生成可复核的中文逐字稿，优先使用 Qwen3-ASR 的标点和段落级时间信息，保留 MLX Whisper 备用。支持按任务整理为包含媒体与时间链接的 Obsidian 笔记。

## 安装

将 `transcript-maker` 目录复制到 `~/.codex/skills/transcript-maker`，按需配置独立 Python 环境和模型。现有同名技能请先比较内容，避免覆盖个人设置。模型和运行环境不包含在仓库内，详见 [本地识别说明](transcript-maker/references/local-asr.md)。

## 使用

在 Codex 中提供本地音视频路径或可正常访问的网页，并说明输出位置；也可以调用 `$transcript-maker`。技能负责识别、检查和整理。输出标为机器初审，仍需回听核对错词、专有名词和异常片段。云端识别仅在用户选择时使用。

```text
请用逐字稿生成 skill 处理这个视频，保存到我指定的 Obsidian 目录。
```

时间链接使用媒体片段语法；Obsidian 是否在当前嵌入播放器精确跳转，取决于客户端，须实际验证。具体使用规则见 [SKILL.md](transcript-maker/SKILL.md)。

## 术语提示

Qwen 默认使用常用词库作为上下文提示，也可按主题选择或关闭。热词可能导致误识别；后处理匹配仅作候选，保留原文并核对。词表与操作说明见 [术语和热词](transcript-maker/references/hotwords.md)。

## 测试记录

一次 M2 Pro 上的 120 秒中文课程测试，Qwen3-ASR 0.6B 使用 chunk 时间戳完成命令约 6.45 秒；词级对齐约 13.92 秒，Whisper large-v3-turbo 词级时间戳约 12.28 秒。均为单次运行，不含下载，材料、时间戳粒度不同，不作为通用速度或准确率结论。Qwen 输出标点较完整但仍有识别错误；词级对齐存在零时长片段。

## 开发

提交前运行 `python3 -m unittest discover -s tests`，并验证 skill frontmatter。不要提交音视频、识别结果、个人路径、模型、凭证或本地虚拟环境。贡献变更时说明测试材料、运行环境、时间戳粒度和未验证范围。
