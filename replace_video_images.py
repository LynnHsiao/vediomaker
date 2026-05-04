#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List


def ensure_ffmpeg() -> None:
    for cmd in ("ffmpeg", "ffprobe"):
        if shutil.which(cmd) is None:
            raise RuntimeError(f"找不到 {cmd}，請先安裝 FFmpeg 套件。")


def run(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def get_video_size(input_path: Path) -> Dict[str, int]:
    probe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        str(input_path),
    ]
    result = run(probe_cmd)
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    return {"width": int(stream["width"]), "height": int(stream["height"])}


def build_filter(specs: List[Dict[str, Any]], base_width: int, base_height: int) -> str:
    chain: List[str] = []
    current = "[0:v]"

    for idx, spec in enumerate(specs):
        x = int(spec.get("x", 0))
        y = int(spec.get("y", 0))
        w = int(spec.get("width", base_width))
        h = int(spec.get("height", base_height))
        start = spec["start"]
        end = spec["end"]
        opacity = float(spec.get("opacity", 1.0))

        img = f"[{idx + 1}:v]"
        resized = f"[img{idx}]"
        with_alpha = f"[img{idx}a]"
        out = f"[v{idx}]"

        chain.append(f"{img}scale={w}:{h}{resized}")
        if opacity < 1.0:
            chain.append(f"{resized}format=rgba,colorchannelmixer=aa={opacity}{with_alpha}")
            overlay_in = with_alpha
        else:
            overlay_in = resized

        chain.append(
            f"{current}{overlay_in}overlay={x}:{y}:enable='between(t,{start},{end})'{out}"
        )
        current = out

    chain.append(f"{current}format=yuv420p[vout]")
    return ";".join(chain)


def main() -> None:
    parser = argparse.ArgumentParser(description="置換影片中的圖片內容並保留原始旁白（音軌）。")
    parser.add_argument("--input", required=True, help="輸入影片")
    parser.add_argument("--config", required=True, help="置換設定 JSON")
    parser.add_argument("--output", required=True, help="輸出影片")
    parser.add_argument("--video-codec", default="libx264")
    parser.add_argument("--crf", default="18")
    parser.add_argument("--preset", default="medium")
    args = parser.parse_args()

    ensure_ffmpeg()

    input_path = Path(args.input)
    output_path = Path(args.output)
    config_path = Path(args.config)

    if not input_path.exists():
        raise FileNotFoundError(f"找不到輸入影片: {input_path}")
    if not config_path.exists():
        raise FileNotFoundError(f"找不到設定檔: {config_path}")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    replacements = config.get("replacements", [])
    if not replacements:
        raise ValueError("設定檔中至少要有一筆 replacements。")

    size = get_video_size(input_path)

    ffmpeg_cmd = ["ffmpeg", "-y", "-i", str(input_path)]
    for rep in replacements:
        image = Path(rep["image"])
        if not image.exists():
            raise FileNotFoundError(f"找不到圖片檔: {image}")
        ffmpeg_cmd += ["-i", str(image)]

    filter_complex = build_filter(replacements, size["width"], size["height"])

    ffmpeg_cmd += [
        "-filter_complex",
        filter_complex,
        "-map",
        "[vout]",
        "-map",
        "0:a?",
        "-c:v",
        args.video_codec,
        "-crf",
        str(args.crf),
        "-preset",
        args.preset,
        "-c:a",
        "copy",
        "-shortest",
        str(output_path),
    ]

    process = subprocess.run(ffmpeg_cmd, text=True)
    if process.returncode != 0:
        raise RuntimeError("FFmpeg 執行失敗，請檢查輸入參數與媒體格式。")

    print(f"完成：{output_path}")


if __name__ == "__main__":
    main()
