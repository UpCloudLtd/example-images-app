import os
import uuid

import boto3
import psycopg
from botocore.exceptions import ClientError
from flask import Flask, Response, jsonify, request

DATABASE_URL = os.environ["DATABASE_URL"]
S3_ENDPOINT_URL = os.environ["S3_ENDPOINT_URL"]
S3_ACCESS_KEY = os.environ["S3_ACCESS_KEY"]
S3_SECRET_KEY = os.environ["S3_SECRET_KEY"]
S3_BUCKET = os.environ["S3_BUCKET"]

app = Flask(__name__)

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name="us-east-1",
)


def db():
    return psycopg.connect(DATABASE_URL)


def init():
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS photos (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                tags TEXT[] NOT NULL DEFAULT '{}',
                object_key TEXT NOT NULL
            )
            """
        )
    try:
        s3.create_bucket(Bucket=S3_BUCKET)
    except ClientError as err:
        if err.response["Error"]["Code"] not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            raise


@app.get("/api/photos")
def list_photos():
    with db() as conn:
        rows = conn.execute(
            "SELECT id, filename, description, tags FROM photos ORDER BY id DESC"
        ).fetchall()
    return jsonify(
        [
            {"id": r[0], "filename": r[1], "description": r[2], "tags": r[3]}
            for r in rows
        ]
    )


@app.post("/api/photos")
def create_photo():
    file = request.files.get("file")
    if file is None or not file.filename:
        return jsonify({"error": "file is required"}), 400

    description = request.form.get("description", "")
    tags = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
    object_key = str(uuid.uuid4())

    s3.upload_fileobj(
        file,
        S3_BUCKET,
        object_key,
        ExtraArgs={"ContentType": file.mimetype or "application/octet-stream"},
    )

    with db() as conn:
        row = conn.execute(
            "INSERT INTO photos (filename, description, tags, object_key)"
            " VALUES (%s, %s, %s, %s) RETURNING id",
            (file.filename, description, tags, object_key),
        ).fetchone()

    return jsonify({"id": row[0], "filename": file.filename, "description": description, "tags": tags}), 201


@app.get("/api/photos/<int:photo_id>/image")
def get_image(photo_id):
    with db() as conn:
        row = conn.execute(
            "SELECT object_key FROM photos WHERE id = %s", (photo_id,)
        ).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404

    obj = s3.get_object(Bucket=S3_BUCKET, Key=row[0])
    return Response(obj["Body"].read(), mimetype=obj.get("ContentType", "application/octet-stream"))


@app.delete("/api/photos/<int:photo_id>")
def delete_photo(photo_id):
    with db() as conn:
        row = conn.execute(
            "DELETE FROM photos WHERE id = %s RETURNING object_key", (photo_id,)
        ).fetchone()
    if row is None:
        return jsonify({"error": "not found"}), 404

    s3.delete_object(Bucket=S3_BUCKET, Key=row[0])
    return jsonify({"id": photo_id})


init()
