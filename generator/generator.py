import logging
import os
import time
from io import BytesIO

import requests
import torch
from diffusers import Flux2KleinPipeline

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:5000").rstrip("/")
GENERATOR_TOKEN = os.environ.get("GENERATOR_TOKEN", "local-generator-token")
POLL_INTERVAL = float(os.environ.get("POLL_INTERVAL", "5"))
IMAGE_MODEL = "black-forest-labs/FLUX.2-klein-4B"
IMAGE_SIZE = (1024, 1024)
IMAGE_INFERENCE_STEPS = 4
IMAGE_DEVICE = os.environ.get("IMAGE_DEVICE", "auto")

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("generator")

api = requests.Session()
api.headers["Authorization"] = f"Bearer {GENERATOR_TOKEN}"
image_pipeline: Flux2KleinPipeline | None = None


def select_device():
    if IMAGE_DEVICE != "auto":
        return IMAGE_DEVICE
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_pipeline():
    global image_pipeline

    if image_pipeline is None:
        device = select_device()
        logger.info("Loading %s on %s", IMAGE_MODEL, device)
        image_pipeline = Flux2KleinPipeline.from_pretrained(
            IMAGE_MODEL,
            torch_dtype=torch.float32 if device == "cpu" else torch.bfloat16,
        ).to(device)
    return image_pipeline


def set_state(image_id: str, state: str, state_details: str):
    return api.patch(
        f"{BACKEND_URL}/api/images/{image_id}",
        json={"state": state, "state_details": state_details},
        timeout=30,
    )


def process(image: dict):
    image_id = image["id"]
    settings = f"{IMAGE_MODEL} at {IMAGE_SIZE[0]}x{IMAGE_SIZE[1]} using {IMAGE_INFERENCE_STEPS} steps"

    response = set_state(image_id, "generating", f"Generating with {settings}.")
    if response.status_code in (404, 409):
        logger.info("Image %s was deleted or claimed by another generator", image_id)
        return
    response.raise_for_status()

    try:
        logger.info("Generating image %s: %s", image_id, image["description"])
        generated = get_pipeline()(
            prompt=image["description"],
            width=IMAGE_SIZE[0],
            height=IMAGE_SIZE[1],
            guidance_scale=1.0,
            num_inference_steps=IMAGE_INFERENCE_STEPS,
        ).images[0]
        image_stream = BytesIO()
        generated.convert("RGB").save(image_stream, format="PNG")
        image_stream.seek(0)

        response = api.put(
            f"{BACKEND_URL}/api/images/{image_id}/image",
            files={"image": ("image.png", image_stream, "image/png")},
            data={"state_details": f"Generated with {settings}."},
            timeout=120,
        )
        response.raise_for_status()
        logger.info("Image %s is ready", image_id)
    except Exception as err:
        logger.exception("Generating image %s failed", image_id)
        set_state(image_id, "error", f"{type(err).__name__}: {err}")


def main():
    logger.info("Polling %s for pending images every %s seconds", BACKEND_URL, POLL_INTERVAL)
    while True:
        try:
            response = api.get(f"{BACKEND_URL}/api/images/pending", params={"model": IMAGE_MODEL}, timeout=30)
            if response.status_code == 204:
                time.sleep(POLL_INTERVAL)
                continue
            response.raise_for_status()
            process(response.json())
        except requests.RequestException as err:
            logger.warning("Backend request failed: %s", err)
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
