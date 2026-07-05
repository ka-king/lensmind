"""LensMind CLI 入口。

用法:
    python -m lensmind.main --product-name "产品名" --product-images img1.jpg img2.jpg
"""

from __future__ import annotations

import argparse
import logging
import sys

__author__ = "万"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("lensmind")


def main():
    """LensMind 命令行入口。"""
    parser = argparse.ArgumentParser(
        description="LensMind — AI 电商视频生成智能体",
    )
    parser.add_argument(
        "--product-name", required=True,
        help="产品名称或描述",
    )
    parser.add_argument(
        "--product-images", nargs="*", default=[],
        help="产品图片路径（可选，支持多张）",
    )
    parser.add_argument(
        "--requirements", default="",
        help="额外视频要求（自然语言）",
    )
    parser.add_argument(
        "--style", default="product_showcase",
        choices=["marketing", "social_media", "tutorial", "product_showcase"],
        help="视频风格（默认 product_showcase）",
    )
    parser.add_argument(
        "--duration", type=int, default=30,
        help="目标视频时长，单位秒（默认 30）",
    )
    parser.add_argument(
        "--config", default=None,
        help="配置文件路径（默认当前目录下的 config.yaml）",
    )

    args = parser.parse_args()

    from lensmind.config.app_config import load_app_config
    from lensmind.client import LensMindClient

    logger.info("LensMind v0.1.0 — 电商视频生成智能体")
    logger.info("产品: %s", args.product_name)
    logger.info("图片: %s", args.product_images or "无")
    logger.info("风格: %s, 时长: %ds", args.style, args.duration)

    config = load_app_config(args.config)
    client = LensMindClient(config=config)

    try:
        result = client.generate_video(
            product_name=args.product_name,
            product_images=args.product_images,
            requirements=args.requirements,
            style=args.style,
            duration_sec=args.duration,
        )

        print(f"\n{'='*60}")
        print(f"状态: {result.get('status', 'unknown')}")

        messages = result.get("messages", [])
        if messages:
            last_ai = messages[-1]
            content = last_ai.content if hasattr(last_ai, 'content') else str(last_ai)
            print(f"\n{content}")

        print(f"\n{'='*60}")

    except Exception as e:
        logger.error("视频生成失败: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
