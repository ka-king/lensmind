"""模型工厂——LLM + 图片生成 + 视频生成。

factory.py       LLM 工厂（OpenAI/Anthropic 反射加载）
image_gen.py     图片生成 Provider（Flux/SD/可灵）
video_gen.py     视频生成 Provider（Runway/可灵/Sora）
"""

from lensmind.models.factory import create_model, create_model_by_config
from lensmind.models.image_gen import BaseImageProvider, MockImageProvider, create_image_provider
from lensmind.models.video_gen import BaseVideoProvider, MockVideoProvider, create_video_provider

__author__ = "万"

__all__ = [
    "create_model", "create_model_by_config",
    "BaseImageProvider", "MockImageProvider", "create_image_provider",
    "BaseVideoProvider", "MockVideoProvider", "create_video_provider",
]
