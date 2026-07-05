---
name: product-video
description: 电商产品视频生成——产品分析→剧本→模特图+场景图(并行)→分镜片段→合成
version: 1.0.0
pipeline:
  nodes:
    - name: product_analysis
      subagent: product_analyzer
      depends_on: []

    - name: script
      subagent: script_writer
      depends_on: [product_analysis]

    - name: model_images
      subagent: model_image_artist
      depends_on: [script]
      parallel_group: image_generation

    - name: scene_images
      subagent: scene_designer
      depends_on: [script]
      parallel_group: image_generation

    - name: clips
      subagent: storyboard_animator
      depends_on: [model_images, scene_images]

    - name: final_video
      subagent: video_editor
      depends_on: [clips]
---

# 电商产品视频生成

## 流程

1. 产品分析 — 提取卖点、目标人群、视觉风格
2. 剧本创作 — 分镜脚本 + 口播文案
3. 图片生成（并行）— 模特展示图 + 背景场景图
4. 视频片段 — 将静态图转为动态片段
5. 成片合成 — 拼接片段 + 配音 + 字幕

## 并行优化

model_images 和 scene_images 属于同一 `image_generation` 并行组，
由 DAG Engine 通过 ThreadPoolExecutor 同时执行。
