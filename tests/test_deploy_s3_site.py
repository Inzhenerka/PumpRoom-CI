import io
import tempfile
import unittest
from pathlib import Path

from scripts.deploy_s3_site import cache_control, upload


class Client:
    def __init__(self, fail=None):
        self.fail = fail
        self.objects = {"assets/old-12345678.js": (b"old", "immutable")}
        self.order = []

    def upload_file(self, filename, bucket, key, ExtraArgs):
        if key == self.fail:
            raise RuntimeError("upload failed")
        self.objects[key] = (Path(filename).read_bytes(), ExtraArgs["CacheControl"])
        self.order.append(key)

    def get_object(self, Bucket, Key):
        body, cache = self.objects[Key]
        return {"Body": io.BytesIO(body), "CacheControl": cache}


class UploadTests(unittest.TestCase):
    def test_asset_failure_does_not_publish_index(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "index.html").write_text("new index")
            (root / "app.js").write_text("new app")
            client = Client(fail="app.js")
            with self.assertRaises(RuntimeError):
                upload(client, "site", root)
            self.assertNotIn("index.html", client.objects)

    def test_index_is_last_and_old_assets_are_retained(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "assets").mkdir()
            (root / "index.html").write_text("new index")
            (root / "assets/app-12345678.js").write_text("new app")
            client = Client()
            self.assertEqual(2, upload(client, "site", root))
            self.assertEqual("index.html", client.order[-1])
            self.assertIn("assets/old-12345678.js", client.objects)
            self.assertEqual("no-cache", client.objects["index.html"][1])
            self.assertIn("immutable", client.objects["assets/app-12345678.js"][1])

    def test_unversioned_files_must_revalidate(self):
        for key in ("index.html", "config.json", "assets/app.js", "service-worker.js"):
            self.assertEqual("no-cache", cache_control(key))


if __name__ == "__main__":
    unittest.main()
