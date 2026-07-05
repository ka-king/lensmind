---
name: product-analyzer
description: AI 分析电商产品——提取卖点、目标人群、视觉风格建议
version: 1.0.0
tags: [analysis, product, ecommerce]
requires: [llm]
inputs:
  product_name: {type: string, description: 产品名称或描述}
  product_images: {type: array, description: 产品图片路径}
outputs:
  category: string
  selling_points: array
  target_audience: string
  visual_style: string
  tone: string
---

# 产品分析师

分析电商产品并提取结构化信息，为下游脚本创作提供输入。

## 输入

- 产品名称
- 产品图片（可选）

## 输出

- 品类
- 核心卖点（3-5个）
- 目标人群
- 建议视觉风格
- 建议语调
