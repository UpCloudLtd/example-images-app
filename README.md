# Image generator demo

Generates 1024x1024 images from text descriptions with [FLUX.2 klein 4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B).

## Run with Docker Compose

```sh
docker compose up --build
```

Open http://localhost:5173. The generator runs on CPU in Docker, which is slow.

## Run the generator locally

To use the Apple Silicon GPU (MPS), run the generator natively and everything else in Docker Compose (requires Python 3.10+):

```sh
./scripts/run-local-generator.sh
```

## Configuration

| Variable          | Description                                          | Default                 |
| ----------------- | ---------------------------------------------------- | ----------------------- |
| `GENERATOR_TOKEN` | Shared token between the backend and the generator   | `local-generator-token` |
| `HF_TOKEN`        | Hugging Face token for model downloads               |                         |
| `IMAGE_DEVICE`    | `auto`, `cpu`, `cuda` or `mps`                       | `auto`                  |
