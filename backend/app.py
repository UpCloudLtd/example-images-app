import os
import uuid

import boto3
from botocore.exceptions import ClientError
from flask import Flask, Response, jsonify, request
from sqlalchemy import Text, create_engine, select, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]
DATABASE_DRIVER = "postgresql+psycopg"
engine = create_engine(make_url(DATABASE_URL).set(drivername=DATABASE_DRIVER))
Session = sessionmaker(bind=engine)
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


class Base(DeclarativeBase):
    pass


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default=text("''"))
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list, server_default=text("'{}'"))
    object_key: Mapped[str] = mapped_column(Text, nullable=False)


def init():
    Base.metadata.create_all(engine)
    try:
        s3.create_bucket(Bucket=S3_BUCKET)
    except ClientError as err:
        if err.response["Error"]["Code"] not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            raise


@app.get("/api/photos")
def list_photos():
    with Session() as session:
        photos = session.scalars(select(Photo).order_by(Photo.id.desc())).all()
    return jsonify(
        [
            {"id": photo.id, "filename": photo.filename, "description": photo.description, "tags": photo.tags}
            for photo in photos
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

    with Session.begin() as session:
        photo = Photo(
            filename=file.filename,
            description=description,
            tags=tags,
            object_key=object_key,
        )
        session.add(photo)
        session.flush()
        photo_id = photo.id

    return jsonify({"id": photo_id, "filename": file.filename, "description": description, "tags": tags}), 201


@app.get("/api/photos/<int:photo_id>/image")
def get_image(photo_id):
    with Session() as session:
        photo = session.get(Photo, photo_id)
        if photo is None:
            return jsonify({"error": "not found"}), 404
        object_key = photo.object_key

    obj = s3.get_object(Bucket=S3_BUCKET, Key=object_key)
    return Response(obj["Body"].read(), mimetype=obj.get("ContentType", "application/octet-stream"))


@app.delete("/api/photos/<int:photo_id>")
def delete_photo(photo_id):
    with Session.begin() as session:
        photo = session.get(Photo, photo_id)
        if photo is None:
            return jsonify({"error": "not found"}), 404
        object_key = photo.object_key
        session.delete(photo)

    s3.delete_object(Bucket=S3_BUCKET, Key=object_key)
    return jsonify({"id": photo_id})


init()
