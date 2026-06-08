"""腾讯云 COS / 阿里云 OSS 对象存储上传"""
import os, hashlib
from pathlib import Path
from qcloud_cos import CosConfig, CosS3Client


def get_cloud_client(db_session=None):
    """读取存储配置，返回 (mode, client_or_none)。mode='local' 时返回 (None, None)。"""
    from database import SessionLocal
    from models.db_models import SystemConfig

    db = db_session or SessionLocal()
    close_db = db_session is None
    try:
        keys = ["storage_mode", "storage_provider", "oss_endpoint", "oss_bucket",
                "oss_access_key_id", "oss_access_key_secret"]
        cfg = {}
        for k in keys:
            row = db.query(SystemConfig).filter(SystemConfig.key == k).first()
            cfg[k] = (row.value or "").strip() if row and row.value else ""

        if cfg.get("storage_mode") != "cloud":
            return "local", None

        provider = cfg.get("storage_provider", "tencent_cos")
        if provider == "tencent_cos":
            bucket = cfg.get("oss_bucket", "")
            secret_id = cfg.get("oss_access_key_id", "")
            secret_key = cfg.get("oss_access_key_secret", "")
            if not all([bucket, secret_id, secret_key]):
                return "local", None
            # 从 bucket 名推断 region（COS 默认使用桶所在区域）
            region = cfg.get("oss_endpoint", "").strip() or "ap-guangzhou"
            if "cos." in region and ".myqcloud.com" in region:
                region = region.split("cos.")[1].split(".myqcloud.com")[0]
            print(f"[CloudStorage] 初始化 COS region={region} bucket={bucket}", flush=True)
            cos_cfg = CosConfig(
                Region=region,
                SecretId=secret_id,
                SecretKey=secret_key,
                Scheme="https",
            )
            client = CosS3Client(cos_cfg)
            return "cloud", (client, bucket)
        return "local", None
    except Exception as e:
        print(f"[CloudStorage] 初始化云存储失败: {e}", flush=True)
        return "local", None
    finally:
        if close_db:
            db.close()


def upload_to_cloud(local_path: str, cloud_key: str, client_and_bucket) -> bool:
    """上传文件到 COS/Oss，成功返回 True"""
    try:
        client, bucket = client_and_bucket
        client.upload_file(
            Bucket=bucket,
            Key=cloud_key,
            LocalFilePath=local_path,
            EnableMD5=False,
        )
        print(f"[CloudStorage] 上传成功: {cloud_key}", flush=True)
        return True
    except Exception as e:
        print(f"[CloudStorage] 上传失败: {cloud_key} -> {e}", flush=True)
        return False


def get_cloud_url(cloud_key: str, client_and_bucket) -> str:
    """获取云存储文件的公开 URL"""
    try:
        client, bucket = client_and_bucket
        # 生成预签名 URL（永久有效 or 1年）
        url = client.get_object_url(Bucket=bucket, Key=cloud_key)
        return url
    except Exception:
        return f"/{cloud_key}"
