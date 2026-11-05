# 标点恢复

当识别输出标点明显不足时，优先使用本地专用标点模型，不使用生成式模型重写讲话。保留原始识别 JSON。可使用 [sherpa-onnx 中英 CT-Transformer](https://github.com/k2-fsa/sherpa-onnx) 模型；明确设置本地模型路径并按项目说明安装依赖。

对于 MLX Whisper JSON，仓库的 `scripts/postprocess_mlx_json.py` 可映射时间并恢复标点。使用 `--help` 查看 `--model` 等参数。它会检查去除标点和空白后正文是否保持一致；校验失败时保留原文并记录回退。逐句核对句界与时间范围，不能将专用标点模型当成人工精校。

仅有 segment 时间戳时以 segment 为最小时间单元，不虚构词级定位。若模型不可用或失败，保留原始标点并说明限制。
