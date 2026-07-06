"""阿里云 OSS 图片上传工具——本地文件 → 公网 URL。"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

__author__ = "万"

logger = logging.getLogger(__name__)


def upload_to_oss(
    local_path: str,
    remote_name: str = "",
    *,
    endpoint: str = "",
    bucket_name: str = "",
    access_key_id: str = "",
    access_key_secret: str = "",
    prefix: str = "images",
) -> str:
    """上传本地图片到阿里云 OSS，返回公网 URL。

    参数:
        local_path: 本地文件路径。
        remote_name: OSS 上的文件名（不含前缀），空则自动生成。
        endpoint: OSS endpoint，默认读 OSS_ENDPOINT 环境变量。
        bucket_name: 桶名，默认读 OSS_BUCKET。
        access_key_id: AccessKey ID，默认读 OSS_ACCESS_KEY_ID。
        access_key_secret: AccessKey Secret，默认读 OSS_ACCESS_KEY_SECRET。
        prefix: OSS 上的目录前缀，默认 "images"。

    返回:
        公网可访问的 URL 字符串（1 小时有效签名 URL）。
    """
    import oss2

    endpoint = endpoint or os.environ.get("OSS_ENDPOINT", "")
    bucket_name = bucket_name or os.environ.get("OSS_BUCKET", "")
    access_key_id = access_key_id or os.environ.get("OSS_ACCESS_KEY_ID", "")
    access_key_secret = access_key_secret or os.environ.get("OSS_ACCESS_KEY_SECRET", "")
    prefix = prefix or os.environ.get("OSS_IMAGE_PREFIX", "images")

    if not all([endpoint, bucket_name, access_key_id, access_key_secret]):
        raise ValueError("OSS 配置不完整，请检查环境变量 OSS_ENDPOINT/OSS_BUCKET/OSS_ACCESS_KEY_ID/OSS_ACCESS_KEY_SECRET")

    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)

    path = Path(local_path)
    if not path.exists():
        raise FileNotFoundError(f"本地文件不存在: {local_path}")

    ext = path.suffix or ".png"
    name = remote_name or f"{uuid.uuid4().hex}{ext}"
    key = f"{prefix}/{name}"

    logger.info("上传 OSS: %s → %s/%s", local_path, bucket_name, key)
    bucket.put_object_from_file(key, str(path))

    # 生成签名 URL（1 小时有效）
    url = bucket.sign_url("GET", key, 3600)
    logger.info("OSS URL: %s", url)
    return url
