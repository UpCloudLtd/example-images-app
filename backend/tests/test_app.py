import unittest
import uuid
from io import BytesIO

from botocore.exceptions import ClientError
from PIL import Image as PILImage
from sqlalchemy import text

import app as api

AUTH = {"Authorization": "Bearer test-token"}
SUFFIX = "[bcdfghjklmnpqrstvwxz2456789]{5}"


def png_bytes():
    stream = BytesIO()
    PILImage.new("RGB", (8, 8), "white").save(stream, format="PNG")
    return stream.getvalue()


def empty_bucket():
    for obj in api.s3.list_objects_v2(Bucket=api.S3_BUCKET).get("Contents", []):
        api.s3.delete_object(Bucket=api.S3_BUCKET, Key=obj["Key"])


def tearDownModule():
    empty_bucket()
    api.s3.delete_bucket(Bucket=api.S3_BUCKET)
    api.Base.metadata.drop_all(api.engine)


class GenerateFilenameTest(unittest.TestCase):
    def test_generate_filename(self):
        cases = [
            ("Riva del Garda", rf"riva-del-garda-{SUFFIX}\.png"),
            ("Donkey running in Helsinki", rf"donkey-running-in-{SUFFIX}\.png"),
            ("Rock & Roll  2026!", rf"rock-roll-2026-{SUFFIX}\.png"),
            ("42", rf"42-{SUFFIX}\.png"),
            ("日本の桜", rf"{SUFFIX}\.png"),
        ]
        for description, pattern in cases:
            with self.subTest(description=description):
                self.assertRegex(api.generate_filename(description), f"^{pattern}$")


class ImagesApiTest(unittest.TestCase):
    def setUp(self):
        with api.engine.begin() as connection:
            connection.execute(text(f"TRUNCATE {api.IMAGES_TABLE}"))
        empty_bucket()
        self.client = api.app.test_client()

    def create_image(self, description="Riva del Garda"):
        response = self.client.post("/api/images", json={"description": description})
        self.assertEqual(response.status_code, 202)
        return response.get_json()

    def claim(self, image_id):
        return self.client.patch(
            f"/api/images/{image_id}",
            json={"state": "generating", "state_details": "Generating."},
            headers=AUTH,
        )

    def upload(self, image_id, data=None):
        return self.client.put(
            f"/api/images/{image_id}/image",
            data={"image": (BytesIO(data or png_bytes()), "image.png", "image/png"), "state_details": "Generated."},
            headers=AUTH,
            content_type="multipart/form-data",
        )

    def test_create_image_queues_pending_image(self):
        image = self.create_image()

        self.assertEqual(str(uuid.UUID(image["id"])), image["id"])
        self.assertEqual(image["state"], "pending")
        self.assertIsNone(image["generated_at"])
        self.assertEqual([item["id"] for item in self.client.get("/api/images").get_json()], [image["id"]])

    def test_create_image_rejects_invalid_description(self):
        for payload in [None, {}, {"description": "  "}, {"description": 1}]:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/api/images", json=payload).status_code, 400)

    def test_generator_endpoints_require_token(self):
        image_id = uuid.uuid4()
        endpoints = [
            ("get", "/api/images/pending"),
            ("patch", f"/api/images/{image_id}"),
            ("put", f"/api/images/{image_id}/image"),
        ]
        for method, path in endpoints:
            for headers in [{}, {"Authorization": "Bearer wrong-token"}]:
                with self.subTest(method=method, path=path, headers=headers):
                    self.assertEqual(getattr(self.client, method)(path, headers=headers).status_code, 401)

    def test_pending_returns_oldest_pending_image(self):
        self.assertEqual(self.client.get("/api/images/pending", headers=AUTH).status_code, 204)

        first = self.create_image("first")
        second = self.create_image("second")
        self.assertEqual(self.client.get("/api/images/pending", headers=AUTH).get_json()["id"], first["id"])

        self.claim(first["id"])
        self.assertEqual(self.client.get("/api/images/pending", headers=AUTH).get_json()["id"], second["id"])

    def test_state_transitions(self):
        image = self.create_image()

        response = self.claim(image["id"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["state"], "generating")
        self.assertEqual(response.get_json()["state_details"], "Generating.")

        self.assertEqual(self.claim(image["id"]).status_code, 409)
        response = self.client.patch(f"/api/images/{image['id']}", json={"state": "ready"}, headers=AUTH)
        self.assertEqual(response.status_code, 400)

        response = self.client.patch(
            f"/api/images/{image['id']}", json={"state": "error", "state_details": "boom"}, headers=AUTH
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["state"], "error")

        self.assertEqual(self.claim(uuid.uuid4()).status_code, 404)
        self.assertEqual(self.claim("not-a-uuid").status_code, 404)

    def test_upload_requires_generating_state(self):
        image = self.create_image()

        self.assertEqual(self.upload(image["id"]).status_code, 409)
        self.assertEqual(self.client.get(f"/api/images/{image['id']}/image").status_code, 409)

    def test_upload_rejects_non_png(self):
        image = self.create_image()
        self.claim(image["id"])

        self.assertEqual(self.upload(image["id"], b"not an image").status_code, 400)

    def test_upload_stores_image_and_marks_ready(self):
        image = self.create_image()
        self.claim(image["id"])
        data = png_bytes()

        response = self.upload(image["id"], data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["state"], "ready")
        self.assertEqual(response.get_json()["state_details"], "Generated.")
        self.assertIsNotNone(response.get_json()["generated_at"])

        disposition = f'inline; filename="{image["filename"]}"'
        stored = api.s3.head_object(Bucket=api.S3_BUCKET, Key=image["id"])
        self.assertEqual(stored["ContentType"], "image/png")
        self.assertEqual(stored["ContentDisposition"], disposition)

        served = self.client.get(f"/api/images/{image['id']}/image")
        self.assertEqual(served.status_code, 200)
        self.assertEqual(served.data, data)
        self.assertEqual(served.content_type, "image/png")
        self.assertEqual(served.headers["Content-Disposition"], disposition)

    def test_delete_removes_image_and_object(self):
        image = self.create_image()
        self.claim(image["id"])
        self.upload(image["id"])

        self.assertEqual(self.client.delete(f"/api/images/{image['id']}").status_code, 200)
        self.assertEqual(self.client.get("/api/images").get_json(), [])
        with self.assertRaises(ClientError):
            api.s3.head_object(Bucket=api.S3_BUCKET, Key=image["id"])


if __name__ == "__main__":
    unittest.main()
