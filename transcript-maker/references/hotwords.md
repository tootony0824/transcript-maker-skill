# 术语和热词

Qwen 的 `--context` 是识别提示，不是训练或强制词典。仅在内容、来源或用户提供的信息支持某些术语时，按主题挑选少量相关词。词表可以复制后由用户维护；未确认的专有名词不应作为事实写入正文。

```bash
CONTEXT="$(python3 transcript-maker/scripts/build_context.py --group ai-development --group english-exams)"
mlx-qwen3-asr /path/to/audio.m4a --language Chinese --context "$CONTEXT" -f json -o /path/to/output
```

自行安装的 skill 使用该 skill 文件夹下的路径；`--vocabulary` 可指定用户私有 JSON 文件，格式见 `assets/vocabulary.json`。脚本按组去重并限制每次 30 个词，限制是保守的操作约束，不是模型的经过测量的最佳值。长音频应基于主题选择，避免把全部词库无差别灌入。

热词可能混入未说出的文字，也可能把近音词引向错误结果。对目标词及不含热词的片段与无提示基线对照，检查误插入和误改；在正式笔记中保留原始 ASR JSON、使用的词组及模型设置。无法验证的术语标记回听。

GitHub 项目 [asr-hotword](https://github.com/HaujetZhao/asr-hotword) 可按发音提出后处理候选，但它会直接替换匹配项。本地小样本中 `cloud CLI → Claude CLI` 有帮助，`cloud 是云 → Claude 是云` 和 `托付 → 托福` 是误改。将其输出仅作候选和复核参考，不直接批量覆盖逐字稿；保留原文和候选变更记录。不存在已验证的全自动纠错。
