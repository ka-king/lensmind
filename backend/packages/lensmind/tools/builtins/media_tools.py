"""Media 生成工具——封装 arc-reel 图片 + OSS 上传 + VEO 视频。

供 model_image_artist / scene_designer / storyboard_animator 子 Agent 调用。
"""

from __future__ import annotations

from langchain_core.tools import tool

__author__ = "万"


@tool
def generate_image(prompt: str) -> str:
    """用 AI 生成一张高质量图片。

    调用 arc-reel (Gemini Image) 生成图片，自动上传到阿里云 OSS 获取公网 URL。

    参数:
        prompt: 英文图片描述，包含模特外貌、姿势、服装、光线、背景等细节。

    返回:
        JSON 字符串，包含 file_path（本地路径）和 oss_url（公网 URL）。
    """
    import json
    from lensmind.models.image_gen import ArcReelProvider

    provider = ArcReelProvider()
    result = provider.generate(prompt)

    oss_url = ""
    try:
        from lensmind.utils.oss_upload import upload_to_oss
        oss_url = upload_to_oss(result.file_path)
    except Exception:
        pass

    return json.dumps({
        "file_path": result.file_path,
        "oss_url": oss_url,
        "prompt_used": prompt,
    }, ensure_ascii=False)


@tool
def generate_video(prompt: str, reference_image_url: str = "") -> str:
    """用 AI 生成一段视频。

    调用 VEO 3.1 生成 8 秒视频，可以使用参考图来保持人物/场景一致性。

    参数:
        prompt: 英文视频描述，包含动作、运镜、风格、光线等细节。
        reference_image_url: 可选的参考图片 HTTPS URL，用于保持角色外观一致。

    返回:
        JSON 字符串，包含 video_path（本地路径）和 duration_sec（时长）。
    """
    import json
    from lensmind.models.video_gen import VEOProvider

    provider = VEOProvider()
    refs = [reference_image_url] if reference_image_url else []
    result = provider.generate(prompt, image_paths=refs, aspect_ratio="9:16")

    return json.dumps({
        "video_path": result.file_path,
        "duration_sec": result.duration_sec,
        "prompt_used": prompt,
    }, ensure_ascii=False)
