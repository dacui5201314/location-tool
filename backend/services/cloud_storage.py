"""腾讯云 COS / 阿里云 OSS 对象存储上传"""
import os, hashlib, json
from datetime import datetime
from pathlib import Path
from qcloud_cos import CosConfig, CosS3Client


# ═══════════════════════════════════════════════════════════════
# 统一存储结果对象
# ═══════════════════════════════════════════════════════════════

class StorageResult:
    """统一对象存储返回结构。"""
    __slots__ = ("ok", "url", "key", "provider", "error", "local_path", "mode")

    def __init__(self, ok=False, url="", key="", provider="", error="", local_path="", mode="local"):
        self.ok = ok
        self.url = url
        self.key = key
        self.provider = provider
        self.error = error
        self.local_path = local_path
        self.mode = mode

    def to_dict(self):
        return {k: getattr(self, k, "") for k in self.__slots__}

    def __repr__(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


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
        url = client.get_object_url(Bucket=bucket, Key=cloud_key)
        return url
    except Exception:
        return f"/{cloud_key}"


def upload_report_to_cloud(local_path: str, cloud_key: str, provider: str = "tencent_cos") -> StorageResult:
    """为报告 HTML 提供结构化云上传结果。失败时保留 local_path，绝不静默成功。"""
    result = StorageResult(mode="local", local_path=local_path)

    try:
        mode, client_data = get_cloud_client()
        if mode != "cloud" or not client_data:
            result.error = "cloud_mode_not_configured"
            return result

        result.mode = "cloud"
        result.provider = provider

        client, bucket = client_data
        try:
            client.upload_file(
                Bucket=bucket,
                Key=cloud_key,
                LocalFilePath=local_path,
                EnableMD5=False,
            )
            url = client.get_object_url(Bucket=bucket, Key=cloud_key)
            result.ok = True
            result.url = url
            result.key = cloud_key
            # 上传成功后清理本地临时文件
            try:
                Path(local_path).unlink(missing_ok=True)
            except Exception:
                pass
        except Exception as upload_err:
            result.ok = False
            result.error = f"upload_failed: {upload_err}"
    except Exception as e:
        result.ok = False
        result.error = f"client_init_failed: {e}"

    return result


def upload_healthcheck_to_cloud() -> StorageResult:
    """上传健康检查文件到 COS，用于后台配置验证。"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    key = f"healthcheck/{ts}.txt"
    tmp = Path(__file__).resolve().parent.parent / "storage" / f"_hc_{ts}.txt"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(f"healthcheck {ts}", encoding="utf-8")

    result = upload_report_to_cloud(str(tmp), key)
    result.key = key  # 确保 key 始终正确

    try:
        tmp.unlink(missing_ok=True)
    except Exception:
        pass

    return result


def backfill_local_reports(dry_run=True) -> list[dict]:
    """扫描本地有 report_file 无 report_url 的记录，补传到 COS。
    返回每条的补传结果列表。
    """
    from database import SessionLocal
    from models.db_models import AnalysisRecord

    results = []
    db = SessionLocal()
    try:
        records = db.query(AnalysisRecord).filter(
            AnalysisRecord.report_file.isnot(None),
            AnalysisRecord.report_file != "",
            AnalysisRecord.report_url.is_(None) | (AnalysisRecord.report_url == ""),
        ).order_by(AnalysisRecord.id).all()

        for rec in records:
            item = {"id": rec.id, "report_file": str(rec.report_file), "dry_run": dry_run}
            if not os.path.exists(rec.report_file):
                item["error"] = "local_file_missing"
                results.append(item)
                continue

            if dry_run:
                item["status"] = "dry_run_would_upload"
                results.append(item)
                continue

            cloud_key = f"reports/backfill_{rec.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            sr = upload_report_to_cloud(rec.report_file, cloud_key)
            item["status"] = "uploaded" if sr.ok else "failed"
            item["url"] = sr.url
            item["error"] = sr.error

            if sr.ok and sr.url:
                rec.report_url = sr.url
                db.commit()

            results.append(item)
    finally:
        db.close()

    return results
