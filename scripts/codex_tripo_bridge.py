#!/usr/bin/env python3
"""Submit a Tripo-ready image to Tripo 3D, with an optional standalone fallback image generator."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any


OPENAI_IMAGE_API_URL = "https://api.openai.com/v1/images/generations"
TRIPO_BASE_URL = "https://api.tripo3d.ai/v2/openapi"
DEFAULT_IMAGE_MODEL = "gpt-image-1.5"
DEFAULT_TRIPO_MODEL_VERSION = "v3.1-20260211"
TRIPO_P1_MODEL_VERSION = "P1-20260311"
TASK_FINAL_STATUSES = {"success", "failed", "cancelled", "banned", "expired"}
CHARACTER_HINTS = (
    "character",
    "person",
    "humanoid",
    "hero",
    "villain",
    "warrior",
    "npc",
    "creature",
    "monster",
    "robot",
    "girl",
    "boy",
    "man",
    "woman",
    "human",
)


class BridgeError(RuntimeError):
    """Raised when the bridge pipeline fails."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a white-background no-shadow reference image and convert it with Tripo 3D."
    )
    parser.add_argument(
        "--prompt",
        help=(
            "Text prompt for standalone fallback image generation. "
            "In normal Codex plugin use, generate the image first with the built-in image tool "
            "and pass it with --image."
        ),
    )
    parser.add_argument(
        "--image",
        help="Existing local image path or remote image URL. Skips standalone image generation.",
    )
    parser.add_argument(
        "--subject-type",
        choices=("auto", "object", "character"),
        default="auto",
        help="Controls whether the bridge enforces character T-pose rules.",
    )
    parser.add_argument(
        "--output-dir",
        help=(
            "Directory where the generated reference image, task metadata, and downloaded "
            "Tripo files will be stored."
        ),
    )
    parser.add_argument(
        "--slug",
        help="Optional folder/file slug. Defaults to a sanitized version of the prompt.",
    )
    parser.add_argument(
        "--asset-name",
        help="Optional logical asset name for batch workflows.",
    )
    parser.add_argument(
        "--style-preset",
        choices=("low_poly", "highly_detailed", "photorealistic", "stylized", "toon", "voxel"),
        help="Optional style label stored in summary metadata.",
    )
    parser.add_argument(
        "--example-image",
        action="append",
        default=[],
        help="Optional example image path or URL stored in summary metadata. Repeat for multiple references.",
    )
    parser.add_argument(
        "--image-model",
        default=DEFAULT_IMAGE_MODEL,
        help=f"Standalone fallback image model. Defaults to {DEFAULT_IMAGE_MODEL}.",
    )
    parser.add_argument(
        "--tripo-model-version",
        default=DEFAULT_TRIPO_MODEL_VERSION,
        help=f"Tripo model version. Defaults to {DEFAULT_TRIPO_MODEL_VERSION}.",
    )
    parser.add_argument(
        "--image-size",
        default="1024x1024",
        help="Standalone fallback image size. Defaults to 1024x1024.",
    )
    parser.add_argument(
        "--image-quality",
        default="high",
        choices=("auto", "low", "medium", "high"),
        help="Standalone fallback image quality.",
    )
    parser.add_argument(
        "--texture-quality",
        default="detailed",
        choices=("standard", "detailed"),
        help="Tripo texture quality.",
    )
    parser.add_argument(
        "--geometry-quality",
        default="detailed",
        choices=("standard", "detailed"),
        help="Tripo geometry quality.",
    )
    parser.add_argument(
        "--orientation",
        default="align_image",
        choices=("default", "align_image"),
        help="Tripo orientation setting.",
    )
    parser.add_argument(
        "--texture-alignment",
        default="original_image",
        choices=("original_image", "geometry"),
        help="Tripo texture alignment.",
    )
    parser.add_argument(
        "--face-limit",
        type=int,
        help="Optional Tripo face limit.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=5.0,
        help="Initial Tripo polling interval in seconds.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1800.0,
        help="Maximum time to wait for Tripo completion in seconds.",
    )
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Generate and save the reference image, but do not call Tripo.",
    )
    parser.add_argument(
        "--no-texture",
        action="store_true",
        help="Disable textured output in Tripo.",
    )
    parser.add_argument(
        "--no-pbr",
        action="store_true",
        help="Disable PBR output in Tripo.",
    )
    parser.add_argument(
        "--compress-geometry",
        action="store_true",
        help="Ask Tripo to compress geometry.",
    )
    parser.add_argument(
        "--generate-parts",
        action="store_true",
        help="Ask Tripo to generate parts.",
    )
    parser.add_argument(
        "--smart-low-poly",
        action="store_true",
        help="Ask Tripo to use smart low poly generation.",
    )
    parser.add_argument(
        "--model-seed",
        type=int,
        help="Optional Tripo model seed.",
    )
    parser.add_argument(
        "--texture-seed",
        type=int,
        help="Optional Tripo texture seed.",
    )
    parser.add_argument(
        "--extra-image-instructions",
        help="Extra instructions appended to the standalone image prompt.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress updates while running.",
    )
    return parser.parse_args()


def log(message: str, *, verbose: bool) -> None:
    if verbose:
        print(message, file=sys.stderr)


def ensure_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise BridgeError(f"Missing required environment variable: {name}")
    return value


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized[:64] or "tripo-asset"


def infer_subject_type(prompt: str | None) -> str:
    if not prompt:
        return "object"
    lowered = prompt.lower()
    return "character" if any(token in lowered for token in CHARACTER_HINTS) else "object"


def build_image_prompt(
    prompt: str,
    subject_type: str,
    extra_instructions: str | None = None,
) -> str:
    common_rules = (
        "Create exactly one subject. "
        "Center it in frame with the full silhouette visible and nothing cropped. "
        "Use a seamless pure white studio background with no scene, no props, no text, "
        "no frame, no pedestal, no border, and no extra objects. "
        "Keep lighting even and neutral. "
        "Use no cast shadow, no contact shadow, and no ambient shadow. "
        "Avoid motion blur, dramatic perspective, and background detail. "
        "Make the subject easy to isolate for image-to-3D conversion."
    )
    if subject_type == "character":
        shape_rules = (
            "Render a full-body character in a strict neutral T-pose: front view, "
            "arms straight out horizontally, palms relaxed, legs slightly apart, "
            "symmetrical posture, clear separation between limbs and torso, "
            "and no pose variation. "
            "Do not crop hands, feet, or head. "
            "Do not cover the body with capes, effects, or accessories that hide the silhouette "
            "unless they are explicitly required."
        )
    else:
        shape_rules = (
            "Render a single object as a clean product-style reference, slightly front three-quarter "
            "view unless the prompt explicitly requests another angle. "
            "Keep the outline readable and the object fully visible."
        )

    prompt_parts = [prompt.strip(), common_rules, shape_rules]
    if extra_instructions:
        prompt_parts.append(extra_instructions.strip())
    return " ".join(part for part in prompt_parts if part)


def make_output_dir(base_dir: str | None, slug: str) -> Path:
    if base_dir:
        output_dir = Path(base_dir).expanduser().resolve()
    else:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        output_dir = (
            Path.home()
            / "Downloads"
            / "codex-3d-asset-output"
            / f"{timestamp}-{slug}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def json_request(
    url: str,
    *,
    method: str = "POST",
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request_headers = dict(headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    request = urllib.request.Request(
        url=url,
        method=method,
        headers=request_headers,
        data=data,
    )
    try:
        with urllib.request.urlopen(request) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return json.loads(response.read().decode(charset))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise BridgeError(f"HTTP {exc.code} for {url}: {body}") from exc
    except urllib.error.URLError as exc:
        raise BridgeError(f"Request failed for {url}: {exc}") from exc


def generate_reference_image(
    *,
    prompt: str,
    subject_type: str,
    extra_instructions: str | None,
    image_model: str,
    image_size: str,
    image_quality: str,
    output_dir: Path,
    openai_api_key: str,
    verbose: bool,
) -> tuple[Path, str, dict[str, Any]]:
    effective_prompt = build_image_prompt(prompt, subject_type, extra_instructions)
    payload = {
        "model": image_model,
        "prompt": effective_prompt,
        "background": "opaque",
        "size": image_size,
        "quality": image_quality,
        "output_format": "jpeg",
        "n": 1,
    }
    log("Generating reference image with standalone image API fallback...", verbose=verbose)
    response = json_request(
        OPENAI_IMAGE_API_URL,
        headers={"Authorization": f"Bearer {openai_api_key}"},
        payload=payload,
    )
    data = (response.get("data") or [{}])[0]
    b64_image = data.get("b64_json")
    if not b64_image:
        raise BridgeError("Standalone image response did not contain data[0].b64_json.")

    image_path = output_dir / "reference.jpg"
    image_path.write_bytes(base64.b64decode(b64_image))
    return image_path, effective_prompt, response


def build_multipart_body(file_path: Path) -> tuple[bytes, str]:
    boundary = f"----CodexTripoBoundary{uuid.uuid4().hex}"
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    file_bytes = file_path.read_bytes()
    parts = [
        f"--{boundary}\r\n".encode("utf-8"),
        (
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8"),
        file_bytes,
        b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    return b"".join(parts), boundary


def guess_tripo_file_type(image_ref: str | Path) -> str:
    ref = str(image_ref).lower()
    if ref.endswith(".png"):
        return "png"
    if ref.endswith(".webp"):
        return "webp"
    if ref.endswith(".jpeg"):
        return "jpeg"
    if ref.endswith(".jpg"):
        return "jpg"
    return "jpg"


def tripo_request(
    path: str,
    *,
    api_key: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return json_request(
        f"{TRIPO_BASE_URL}{path}",
        method=method,
        headers={"Authorization": f"Bearer {api_key}"},
        payload=payload,
    )


def upload_image_to_tripo(image_path: Path, *, api_key: str, verbose: bool) -> str:
    log("Uploading reference image to Tripo via /upload/sts...", verbose=verbose)
    body, boundary = build_multipart_body(image_path)
    request = urllib.request.Request(
        url=f"{TRIPO_BASE_URL}/upload/sts",
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        data=body,
    )
    try:
        with urllib.request.urlopen(request) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            payload = json.loads(response.read().decode(charset))
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise BridgeError(f"Tripo upload failed with HTTP {exc.code}: {body_text}") from exc

    image_token = ((payload.get("data") or {}).get("image_token") or "").strip()
    if not image_token:
        raise BridgeError("Tripo upload response did not include data.image_token.")
    return image_token


def create_tripo_task(
    *,
    image_token: str,
    image_type: str,
    api_key: str,
    model_version: str,
    texture_quality: str,
    geometry_quality: str,
    texture_alignment: str,
    orientation: str,
    face_limit: int | None,
    texture: bool,
    pbr: bool,
    compress_geometry: bool,
    generate_parts: bool,
    smart_low_poly: bool,
    model_seed: int | None,
    texture_seed: int | None,
    verbose: bool,
) -> str:
    if model_version == TRIPO_P1_MODEL_VERSION:
        if generate_parts:
            raise BridgeError("generate_parts is not supported for model_version=P1-20260311.")
        if smart_low_poly:
            raise BridgeError("smart_low_poly is not supported for model_version=P1-20260311.")
    elif generate_parts and (texture or pbr):
        raise BridgeError(
            "generate_parts is only supported with texture=false and pbr=false, per Tripo docs."
        )

    payload: dict[str, Any] = {
        "type": "image_to_model",
        "file": {
            "type": image_type,
            "file_token": image_token,
        },
        "model_version": model_version,
        "texture": texture,
        "pbr": pbr,
        "texture_quality": texture_quality,
        "texture_alignment": texture_alignment,
        "orientation": orientation,
    }
    if model_version != TRIPO_P1_MODEL_VERSION:
        payload["geometry_quality"] = geometry_quality
    if face_limit is not None:
        payload["face_limit"] = face_limit
    if compress_geometry:
        payload["compress"] = "geometry"
    if generate_parts:
        payload["generate_parts"] = True
    if smart_low_poly:
        payload["smart_low_poly"] = True
    if model_seed is not None:
        payload["model_seed"] = model_seed
    if texture_seed is not None:
        payload["texture_seed"] = texture_seed

    log("Creating Tripo image_to_model task...", verbose=verbose)
    response = tripo_request("/task", api_key=api_key, method="POST", payload=payload)
    task_id = (((response.get("data") or {}).get("task_id")) or "").strip()
    if not task_id:
        raise BridgeError("Tripo task creation response did not include data.task_id.")
    return task_id


def get_tripo_task(task_id: str, *, api_key: str) -> dict[str, Any]:
    response = tripo_request(f"/task/{task_id}", api_key=api_key)
    task_data = response.get("data")
    if not isinstance(task_data, dict):
        raise BridgeError("Tripo task lookup response did not include a data object.")
    return task_data


def wait_for_tripo_task(
    task_id: str,
    *,
    api_key: str,
    initial_poll_interval: float,
    timeout: float,
    verbose: bool,
) -> dict[str, Any]:
    started_at = time.monotonic()
    poll_interval = max(2.0, initial_poll_interval)

    while True:
        task_data = get_tripo_task(task_id, api_key=api_key)
        status = str(task_data.get("status", "unknown"))
        progress = task_data.get("progress")
        remaining = task_data.get("running_left_time")

        if verbose:
            progress_text = f"{progress}%" if progress is not None else "?"
            remaining_text = f", eta={remaining}s" if remaining is not None else ""
            print(
                f"[Tripo] task={task_id} status={status} progress={progress_text}{remaining_text}",
                file=sys.stderr,
            )

        if status in TASK_FINAL_STATUSES:
            return task_data

        if time.monotonic() - started_at > timeout:
            raise BridgeError(f"Timed out while waiting for Tripo task {task_id}.")

        if isinstance(remaining, (int, float)) and remaining > 0:
            poll_interval = max(2.0, min(30.0, float(remaining) * 0.5))
        else:
            poll_interval = min(30.0, poll_interval * 1.5)
        time.sleep(poll_interval)


def download_file(url: str, destination: Path, *, bearer_token: str, verbose: bool) -> None:
    log(f"Downloading {url} -> {destination}", verbose=verbose)
    request = urllib.request.Request(
        url=url,
        headers={"Authorization": f"Bearer {bearer_token}"},
    )
    try:
        with urllib.request.urlopen(request) as response:
            destination.write_bytes(response.read())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise BridgeError(f"Download failed with HTTP {exc.code} for {url}: {body_text}") from exc
    except urllib.error.URLError as exc:
        raise BridgeError(f"Download failed for {url}: {exc}") from exc


def download_tripo_outputs(
    task_data: dict[str, Any],
    *,
    api_key: str,
    output_dir: Path,
    verbose: bool,
) -> dict[str, str]:
    output = task_data.get("output") or {}
    if not isinstance(output, dict):
        return {}

    downloads: dict[str, str] = {}
    candidates = {
        "model": output.get("model"),
        "base_model": output.get("base_model"),
        "pbr_model": output.get("pbr_model"),
        "generated_image": output.get("generated_image"),
        "rendered_image": output.get("rendered_image"),
    }
    for name, url in candidates.items():
        if not isinstance(url, str) or not url.strip():
            continue
        clean_url = url.strip()
        suffix = Path(clean_url.split("?")[0]).suffix or (
            ".jpg" if name in {"generated_image", "rendered_image"} else ".glb"
        )
        destination = output_dir / f"{task_data['task_id']}_{name}{suffix}"
        download_file(clean_url, destination, bearer_token=api_key, verbose=verbose)
        downloads[name] = str(destination)
    return downloads


def resolve_reference_image(
    *,
    args: argparse.Namespace,
    output_dir: Path,
    openai_api_key: str | None,
) -> tuple[str | Path, str | None, dict[str, Any] | None, str]:
    if args.image:
        if args.image.startswith(("http://", "https://")):
            return args.image, None, None, "remote"

        source_path = Path(args.image).expanduser().resolve()
        if not source_path.exists():
            raise BridgeError(f"Image path does not exist: {source_path}")
        destination = output_dir / source_path.name
        destination.write_bytes(source_path.read_bytes())
        return destination, None, None, "local"

    if not args.prompt:
        raise BridgeError("You must provide --prompt when --image is not set.")
    if not openai_api_key:
        raise BridgeError(
            "Missing OPENAI_API_KEY. In normal Codex plugin use, generate the reference image "
            "with the built-in Codex image tool first, then rerun with --image <path-or-url>. "
            "OPENAI_API_KEY is only needed for standalone --prompt mode."
        )

    subject_type = args.subject_type
    if subject_type == "auto":
        subject_type = infer_subject_type(args.prompt)
    image_path, effective_prompt, raw_response = generate_reference_image(
        prompt=args.prompt,
        subject_type=subject_type,
        extra_instructions=args.extra_image_instructions,
        image_model=args.image_model,
        image_size=args.image_size,
        image_quality=args.image_quality,
        output_dir=output_dir,
        openai_api_key=openai_api_key,
        verbose=args.verbose,
    )
    return image_path, effective_prompt, raw_response, "generated"


def main() -> int:
    args = parse_args()
    slug_source = args.slug or args.prompt or Path(args.image or "codex-3d-asset").stem
    slug = slugify(slug_source)
    output_dir = make_output_dir(args.output_dir, slug)

    try:
        tripo_api_key = None
        if not args.generate_only:
            tripo_api_key = ensure_env("TRIPO_API_KEY")
            if not tripo_api_key.startswith("tsk_"):
                raise BridgeError("TRIPO_API_KEY must start with 'tsk_'.")

        openai_api_key = os.environ.get("OPENAI_API_KEY", "").strip() or None

        reference_image, effective_prompt, openai_response, image_source = resolve_reference_image(
            args=args,
            output_dir=output_dir,
            openai_api_key=openai_api_key,
        )

        summary: dict[str, Any] = {
            "output_dir": str(output_dir),
            "asset_name": args.asset_name,
            "image_source": image_source,
            "reference_image": str(reference_image),
            "prompt": args.prompt,
            "effective_image_prompt": effective_prompt,
            "subject_type": args.subject_type if args.subject_type != "auto" else infer_subject_type(args.prompt),
            "style_preset": args.style_preset,
            "example_images": args.example_image,
            "standalone_image_model": args.image_model if image_source == "generated" else None,
            "tripo_model_version": None if args.generate_only else args.tripo_model_version,
            "downloads": {},
            "task": None,
        }

        if openai_response is not None:
            (output_dir / "standalone-image-response.json").write_text(
                json.dumps(openai_response, indent=2) + "\n",
                encoding="utf-8",
            )

        if args.generate_only:
            summary_path = output_dir / "summary.json"
            summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(summary, indent=2))
            return 0

        if image_source == "remote":
            if args.tripo_model_version == TRIPO_P1_MODEL_VERSION:
                if args.generate_parts:
                    raise BridgeError("generate_parts is not supported for model_version=P1-20260311.")
                if args.smart_low_poly:
                    raise BridgeError("smart_low_poly is not supported for model_version=P1-20260311.")
            elif args.generate_parts and (not args.no_texture or not args.no_pbr):
                raise BridgeError(
                    "generate_parts is only supported with --no-texture and --no-pbr, per Tripo docs."
                )

            file_payload = {
                "type": guess_tripo_file_type(reference_image),
                "url": reference_image,
            }
            log("Using remote reference image URL directly with Tripo.", verbose=args.verbose)
            task_payload = {
                "type": "image_to_model",
                "file": file_payload,
                "model_version": args.tripo_model_version,
                "texture": not args.no_texture,
                "pbr": not args.no_pbr,
                "texture_quality": args.texture_quality,
                "texture_alignment": args.texture_alignment,
                "orientation": args.orientation,
                **({"face_limit": args.face_limit} if args.face_limit is not None else {}),
                **({"compress": "geometry"} if args.compress_geometry else {}),
                **({"generate_parts": True} if args.generate_parts else {}),
                **({"smart_low_poly": True} if args.smart_low_poly else {}),
                **({"model_seed": args.model_seed} if args.model_seed is not None else {}),
                **({"texture_seed": args.texture_seed} if args.texture_seed is not None else {}),
            }
            if args.tripo_model_version != TRIPO_P1_MODEL_VERSION:
                task_payload["geometry_quality"] = args.geometry_quality
            create_response = tripo_request(
                "/task",
                api_key=tripo_api_key,
                method="POST",
                payload=task_payload,
            )
            task_id = (((create_response.get("data") or {}).get("task_id")) or "").strip()
            if not task_id:
                raise BridgeError("Tripo task creation response did not include data.task_id.")
        else:
            image_token = upload_image_to_tripo(reference_image, api_key=tripo_api_key, verbose=args.verbose)
            task_id = create_tripo_task(
                image_token=image_token,
                image_type=guess_tripo_file_type(reference_image),
                api_key=tripo_api_key,
                model_version=args.tripo_model_version,
                texture_quality=args.texture_quality,
                geometry_quality=args.geometry_quality,
                texture_alignment=args.texture_alignment,
                orientation=args.orientation,
                face_limit=args.face_limit,
                texture=not args.no_texture,
                pbr=not args.no_pbr,
                compress_geometry=args.compress_geometry,
                generate_parts=args.generate_parts,
                smart_low_poly=args.smart_low_poly,
                model_seed=args.model_seed,
                texture_seed=args.texture_seed,
                verbose=args.verbose,
            )

        task_data = wait_for_tripo_task(
            task_id,
            api_key=tripo_api_key,
            initial_poll_interval=args.poll_interval,
            timeout=args.timeout,
            verbose=args.verbose,
        )
        summary["task"] = task_data

        status = str(task_data.get("status", "unknown"))
        if status != "success":
            summary_path = output_dir / "summary.json"
            summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(summary, indent=2))
            return 1

        downloads = download_tripo_outputs(
            task_data,
            api_key=tripo_api_key,
            output_dir=output_dir,
            verbose=args.verbose,
        )
        summary["downloads"] = downloads

        summary_path = output_dir / "summary.json"
        summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 0
    except BridgeError as exc:
        error_payload = {
            "error": str(exc),
            "output_dir": str(output_dir),
        }
        print(json.dumps(error_payload, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
