import hmac
import logging
import os
import re
import secrets
import uuid
from datetime import datetime, timezone
from functools import wraps
from io import BytesIO

import boto3
from botocore.exceptions import ClientError
from flask import Flask, Response, jsonify, request
from PIL import Image as PILImage
from sqlalchemy import CheckConstraint, DateTime, Text, create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://images:images@localhost:5432/images")
DATABASE_DRIVER = "postgresql+psycopg"
engine = create_engine(make_url(DATABASE_URL).set(drivername=DATABASE_DRIVER))
Session = sessionmaker(bind=engine)
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "rustfsadmin")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "rustfsadmin")
S3_BUCKET = os.environ.get("S3_BUCKET", "images")
GENERATOR_TOKEN = os.environ.get("GENERATOR_TOKEN", "")
# States the generator may set, mapped to the states they may be set from.
GENERATOR_STATE_TRANSITIONS = {"generating": {"pending"}, "error": {"pending", "generating"}}
# Same alphabet as Kubernetes generated name suffixes: no vowels or look-alike characters.
FILENAME_SUFFIX_ALPHABET = "bcdfghjklmnpqrstvwxz2456789"

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name="us-east-1",
)


class Base(DeclarativeBase):
    pass


class Image(Base):
    __tablename__ = "images"
    __table_args__ = (
        CheckConstraint("state IN ('pending', 'generating', 'ready', 'error')", name="images_state_check"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default=text("''"))
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False, default="pending", server_default=text("'pending'"))
    state_details: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default=text("''"))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


def init():
    Base.metadata.create_all(engine)
    try:
        s3.create_bucket(Bucket=S3_BUCKET)
    except ClientError as err:
        if err.response["Error"]["Code"] not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            raise


def image_to_dict(image: Image):
    return {
        "id": image.id,
        "filename": image.filename,
        "description": image.description,
        "state": image.state,
        "state_details": image.state_details,
        "requested_at": image.requested_at.isoformat(),
        "generated_at": image.generated_at.isoformat() if image.generated_at else None,
    }


def generate_filename(description: str):
    slug = re.sub(r"\s+", "-", description.lower())
    slug = re.sub(r"[^a-z-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")[:18].rstrip("-")
    suffix = "".join(secrets.choice(FILENAME_SUFFIX_ALPHABET) for _ in range(5))
    return f"{slug}-{suffix}.png" if slug else f"{suffix}.png"


def require_generator_token(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        provided = request.headers.get("Authorization", "").encode()
        expected = f"Bearer {GENERATOR_TOKEN}".encode()
        if not GENERATOR_TOKEN or not hmac.compare_digest(provided, expected):
            return jsonify({"error": "unauthorized"}), 401
        return view(*args, **kwargs)

    return wrapper


@app.get("/api/images")
def list_images():
    with Session() as session:
        images = session.scalars(select(Image).order_by(Image.id.desc())).all()
    return jsonify([image_to_dict(image) for image in images])


@app.get("/api/images/pending")
@require_generator_token
def get_oldest_pending_image():
    with Session() as session:
        image = session.scalars(
            select(Image).where(Image.state == "pending").order_by(Image.requested_at, Image.id).limit(1)
        ).first()
        if image is None:
            return "", 204
        return jsonify(image_to_dict(image))


@app.patch("/api/images/<int:image_id>")
@require_generator_token
def update_image_state(image_id):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON body is required"}), 400

    state = payload.get("state")
    state_details = payload.get("state_details", "")
    if state not in GENERATOR_STATE_TRANSITIONS:
        return jsonify({"error": f"state must be one of: {', '.join(GENERATOR_STATE_TRANSITIONS)}"}), 400
    if not isinstance(state_details, str):
        return jsonify({"error": "state_details must be a string"}), 400

    with Session.begin() as session:
        image = session.get(Image, image_id, with_for_update=True)
        if image is None:
            return jsonify({"error": "not found"}), 404
        if image.state not in GENERATOR_STATE_TRANSITIONS[state]:
            return jsonify({"error": f"cannot change state from {image.state} to {state}"}), 409
        image.state = state
        image.state_details = state_details
        result = image_to_dict(image)

    return jsonify(result)


@app.post("/api/images")
def create_image():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "JSON body is required"}), 400

    description = payload.get("description", "")
    if not isinstance(description, str):
        return jsonify({"error": "description must be a string"}), 400

    description = description.strip()
    if not description:
        return jsonify({"error": "description is required"}), 400

    object_key = str(uuid.uuid4())
    filename = generate_filename(description)
    requested_at = datetime.now(timezone.utc)

    with Session.begin() as session:
        image = Image(
            filename=filename,
            description=description,
            object_key=object_key,
            state="pending",
            state_details="Queued for generation.",
            requested_at=requested_at,
        )
        session.add(image)
        session.flush()
        result = image_to_dict(image)

    return jsonify(result), 202


@app.get("/api/images/<int:image_id>/image")
def get_image(image_id):
    with Session() as session:
        image = session.get(Image, image_id)
        if image is None:
            return jsonify({"error": "not found"}), 404
        if image.state != "ready":
            return jsonify({"error": "image is not ready", "state_details": image.state_details}), 409
        object_key = image.object_key

    obj = s3.get_object(Bucket=S3_BUCKET, Key=object_key)
    headers = {"Content-Disposition": obj["ContentDisposition"]} if obj.get("ContentDisposition") else None
    return Response(
        obj["Body"].read(),
        mimetype=obj.get("ContentType", "application/octet-stream"),
        headers=headers,
    )


@app.put("/api/images/<int:image_id>/image")
@require_generator_token
def upload_image(image_id):
    upload = request.files.get("image")
    state_details = request.form.get("state_details", "")
    if upload is None:
        return jsonify({"error": "image file is required"}), 400

    data = upload.read()
    try:
        with PILImage.open(BytesIO(data)) as uploaded:
            image_format = uploaded.format
            uploaded.verify()
    except Exception:
        return jsonify({"error": "image must be a valid PNG"}), 400
    if image_format != "PNG":
        return jsonify({"error": "image must be a valid PNG"}), 400

    with Session() as session:
        image = session.get(Image, image_id)
        if image is None:
            return jsonify({"error": "not found"}), 404
        if image.state != "generating":
            return jsonify({"error": f"cannot upload image in state {image.state}"}), 409
        object_key = image.object_key
        filename = image.filename

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=object_key,
        Body=data,
        ContentType="image/png",
        ContentDisposition=f'inline; filename="{filename}"',
    )

    with Session.begin() as session:
        image = session.get(Image, image_id, with_for_update=True)
        if image is None:
            s3.delete_object(Bucket=S3_BUCKET, Key=object_key)
            return jsonify({"error": "not found"}), 404
        if image.state != "generating":
            return jsonify({"error": f"cannot upload image in state {image.state}"}), 409
        image.state = "ready"
        image.state_details = state_details
        image.generated_at = datetime.now(timezone.utc)
        result = image_to_dict(image)

    return jsonify(result)


@app.delete("/api/images/<int:image_id>")
def delete_image(image_id):
    with Session.begin() as session:
        image = session.get(Image, image_id)
        if image is None:
            return jsonify({"error": "not found"}), 404
        object_key = image.object_key
        session.delete(image)

    s3.delete_object(Bucket=S3_BUCKET, Key=object_key)
    return jsonify({"id": image_id})


init()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
