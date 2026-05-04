# 影片內容圖片置換工具（保留旁白）

這個工具可以在**不改動原始音訊（旁白）**的前提下，將影片中的指定區段替換成新的圖片。

## 功能
- 依照時間區段把畫面替換成指定圖片。
- 可選擇是否保留原畫面的透明度（`opacity`）。
- 最終輸出直接沿用原始影片音軌，確保旁白不受影響。

## 需求
- Python 3.9+
- 系統可執行 `ffmpeg` 與 `ffprobe`

## 安裝
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 使用方式
1. 建立設定檔（例如 `replacements.json`）：

```json
{
  "replacements": [
    {
      "image": "assets/slide1_new.png",
      "start": "00:00:03.0",
      "end": "00:00:08.5",
      "x": 0,
      "y": 0,
      "width": 1280,
      "height": 720,
      "opacity": 1.0
    }
  ]
}
```

2. 執行：
```bash
python replace_video_images.py \
  --input input.mp4 \
  --config replacements.json \
  --output output.mp4
```

## 參數說明
- `--input`: 原始影片路徑
- `--config`: 置換規則 JSON
- `--output`: 輸出影片路徑
- `--video-codec`: 視訊編碼器（預設 `libx264`）
- `--crf`: 輸出品質（預設 `18`）
- `--preset`: 編碼速度/壓縮率（預設 `medium`）

## 注意事項
- 若只想單純「整段蓋掉畫面」並保留旁白，可把 `x,y,width,height` 設成全畫面。
- 多個 replacement 可以同時指定，會按照設定順序套用。
