# Review #015 — Script Writer 命名决策（不重命名）

**Reviewer**: 万
**Date**: 2026-07-05
**Status**: ✅ 保持 `script_writer`，不重命名

---

## Review 过程

Review 建议将 `script_writer` 重命名为 `storyboard_compiler`，因为实际职责
超出了"写剧本"——包含时间调度、多模态 prompt 生成、运镜控制。

## 决策

保持 `script_writer`，不重命名。

## 原因

- 当前阶段不需要为"准确性"支付重命名的上下文切换成本
- 6 个子 Agent 的命名风格保持一致（product_analyzer / scene_designer / video_editor...），突然改一个破坏一致性
- 等整个 pipeline 的 IR schema 明确落地后，再考虑是否需要重命名

## 保留的改进

Prompt 文件 `prompts/script_writer.md` 的内部结构改进保留了：
- 三层标注（policy layer / semantic layer / execution spec）
- 更清晰的下游消费指引

文件名、变量名、注册名均保持 `script_writer`。

---

## 教训

Review 建议不等于必须执行。命名改动的波及面大（8+ 文件），
应该先确认方向再动手。
