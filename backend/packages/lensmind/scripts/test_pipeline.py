"""一次测试：arc-reel 图片 → OSS 上传 → VEO 视频。"""

from __future__ import annotations

import os
import sys

# 添加 packages 到 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv()

from lensmind.models.image_gen import ArcReelProvider
from lensmind.models.video_gen import VEOProvider
from lensmind.utils.oss_upload import upload_to_oss

__author__ = "万"


def main():
    product = "法式复古碎花连衣裙"
    model_desc = (
        "A beautiful Asian female model wearing an elegant floral dress, "
        "standing confidently, full body shot, professional fashion photography, "
        "clean white background, soft studio lighting, high quality"
    )

    print("=" * 60)
    print(f"测试链路: arc-reel → OSS → VEO")
    print(f"产品: {product}")
    print("=" * 60)

    # Step 1: 生成模特图
    print("\n[1/3] 生成模特图...")
    img = ArcReelProvider()
    result = img.generate(model_desc)
    print(f"   图片: {result.file_path}")

    # Step 2: 上传 OSS
    print("\n[2/3] 上传 OSS...")
    url = upload_to_oss(result.file_path, remote_name="test_model_ref.png")
    print(f"   URL: {url}")

    # Step 3: 生成视频（带参考图）
    print("\n[3/3] 生成视频...")
    prompt = (
        f"The same model wearing the {product}, walking gracefully toward camera, "
        "then turning around to show the back of the dress, smooth cinematic camera movement, "
        "natural lighting, professional fashion film style"
    )
    veo = VEOProvider()
    video = veo.generate(
        prompt,
        image_paths=[url],  # ← OSS URL 作为参考图
        duration_sec=8,
        aspect_ratio="9:16",
    )
    print(f"   视频: {video.file_path}")

    print(f"\n{'=' * 60}")
    print("完整链路测试通过!")
    print(f"   图片: {result.file_path}")
    print(f"   OSS:  {url}")
    print(f"   视频: {video.file_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
