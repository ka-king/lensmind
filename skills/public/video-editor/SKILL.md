---
name: video-editor
description: 视频剪辑——拼接片段+配音+字幕+背景音乐→最终视频
version: 1.0.0
tags: [video, editing, ecommerce]
requires: [llm, tts, bash]
---

# 剪辑师

将分镜片段、配音、字幕和背景音乐合成为最终视频。

使用 FFmpeg 执行：
1. concat demuxer 拼接片段
2. 叠加配音音频
3. burn subtitles 烧录字幕
4. amix 混合背景音乐
