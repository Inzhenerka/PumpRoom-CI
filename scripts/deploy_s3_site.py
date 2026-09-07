"""Upload a static build without CDN; publish index last and retain old assets."""
from __future__ import annotations

import argparse
import concurrent.futures
import mimetypes
import re
from pathlib import Path


def cache_control(path: str) -> str:
    if re.match(r"^assets/.+-[A-Za-z0-9_-]{8,}\.[^/]+$", path):
        return "public,max-age=31536000,immutable"
    return "no-cache"


def files_to_upload(dist: Path) -> list[Path]:
    if not (dist / "index.html").is_file():
        raise ValueError(f"Missing {dist / 'index.html'}")
    files = sorted(p for p in dist.rglob("*") if p.is_file())
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(dist.resolve()):
            raise ValueError("Build must not contain symlinks outside the output directory")
        if any(part.startswith(".") for part in path.relative_to(dist).parts):
            raise ValueError(f"Refusing to publish hidden file {path.name}")
    return files


def upload(client, bucket: str, dist: Path) -> int:
    files = files_to_upload(dist)
    index = dist / "index.html"

    def put(path: Path):
        key = path.relative_to(dist).as_posix()
        content_type = mimetypes.guess_type(key)[0] or "application/octet-stream"
        if path.suffix in (".js", ".mjs"):
            content_type = "application/javascript"
        client.upload_file(str(path), bucket, key, ExtraArgs={
            "ContentType": content_type,
            "CacheControl": cache_control(key),
        })

    # Await every upload; index remains unchanged if any prerequisite fails.
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(put, [p for p in files if p != index]))
    put(index)
    # Read back using the same restricted account and verify bytes + metadata.
    for path in files:
        key = path.relative_to(dist).as_posix()
        response = client.get_object(Bucket=bucket, Key=key)
        if response["Body"].read() != path.read_bytes() or response.get("CacheControl") != cache_control(key):
            raise RuntimeError(f"S3 read-back verification failed: {key}")
    return len(files)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--dist", type=Path, required=True)
    args = parser.parse_args()
    import boto3
    client = boto3.client("s3", endpoint_url="https://storage.yandexcloud.net", region_name="ru-central1")
    count = upload(client, args.bucket, args.dist)
    print(f"Uploaded and read-back verified {count} objects; index.html published last. Old assets retained.")
