---
name: paddleocr-windows-setup
description: >
  Install and configure PaddleOCR on Windows for Chinese text OCR. Covers Python 3.12 venv setup,
  critical PaddlePaddle/PaddleOCR version compatibility (must use PaddlePaddle 3.0.0, not 3.3.1),
  Tsinghua mirror acceleration, PyMuPDF for PDF conversion, model cache clearing, and the new
  PaddleOCR 3.x API format (dict with rec_texts/rec_scores). Use when the user needs to set up
  PaddleOCR locally or encounters oneDNN NotImplementedError or compatibility issues.
---

# PaddleOCR Windows Setup

Install and configure PaddleOCR for Chinese text OCR on Windows.

## Prerequisites

- Python 3.12 (managed install preferred)
- Windows with Git Bash or PowerShell

## Installation

### 1. Create Virtual Environment

```bash
~/.workbuddy/binaries/python/versions/3.13.12/python.exe -m venv ~/.workbuddy/binaries/python/envs/paddleocr
```

Use the highest available Python 3.12+ version.

### 2. Install Packages (Tsinghua Mirror)

Use `https://pypi.tuna.tsinghua.edu.cn/simple` for all pip installs — it is ~30x faster on Chinese networks.

**CRITICAL version compatibility**: PaddleOCR 3.6+ with PaddlePaddle 3.3.1 causes a oneDNN error:
```
NotImplementedError: ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]
```
**Must use PaddlePaddle 3.0.0 (exactly):**

```bash
PIP="~/.workbuddy/binaries/python/envs/paddleocr/Scripts/pip"
MIRROR="-i https://pypi.tuna.tsinghua.edu.cn/simple"

$PIP install paddlepaddle==3.0.0 $MIRROR
$PIP install paddleocr $MIRROR
$PIP install PyMuPDF $MIRROR
```

### 3. Verify

```bash
~/.workbuddy/binaries/python/envs/paddleocr/Scripts/python -c "from paddleocr import PaddleOCR; print('OK')"
```

## Model Caching

First use of PaddleOCR downloads 5 models to `~/.paddlex/official_models/`:

| Model | Size | Purpose |
|-------|------|---------|
| PP-LCNet_x1_0_doc_ori | ~6MB | Document orientation |
| UVDoc | ~30MB | Document unwarping |
| PP-LCNet_x1_0_textline_ori | ~5MB | Text line orientation |
| PP-OCRv5_server_det | ~84MB | Text detection |
| PP-OCRv5_server_rec | ~80MB | Text recognition |

Total ~205MB. First OCR call initializes all 5 models (slow, ~1-2 minutes).

**Model cache clearance**: If downgrading PaddlePaddle or encountering errors, delete the cache:
```bash
rm -rf ~/.paddlex/official_models/
```

## API Usage (PaddleOCR 3.x)

The PaddleOCR 3.x API returns a list of dicts, NOT the old nested list format.

```python
import os, warnings
os.environ['GLOG_minloglevel'] = '2'  # suppress Paddle logs
os.environ['FLAGS_use_mkldnn'] = '0'  # disable oneDNN
warnings.filterwarnings('ignore')

from paddleocr import PaddleOCR

ocr = PaddleOCR(lang='ch')  # lazy-singleton pattern recommended
result = ocr.ocr('image.png')

# result[0] is a dict with keys:
#   rec_texts: list[str] — recognized text
#   rec_scores: list[float] — confidence scores
#   dt_polys: list — detection polygons
#   doc_preprocessor_res: dict — orientation/unwarping result

item = result[0]
texts = item['rec_texts']
scores = item['rec_scores']

for t, s in zip(texts, scores):
    print(f'{t} ({s:.2f})')
```

## PDF Processing

```python
import fitz  # PyMuPDF

def pdf_to_images(pdf_path, dpi=200):
    doc = fitz.open(pdf_path)
    images = []
    for i in range(doc.page_count):
        pix = doc[i].get_pixmap(dpi=dpi)
        img_path = f'page_{i+1}.png'
        pix.save(img_path)
        images.append(img_path)
    doc.close()
    return images
```

## Performance

- First OCR call: ~60-120 seconds (model loading + warmup)
- Subsequent calls: ~30-60 seconds per page (depends on document complexity)
- 200 DPI is a good default for medical documents
- 18-page PDF takes ~20-30 minutes on CPU

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `NotImplementedError: ConvertPirAttribute2RuntimeAttribute` | PaddlePaddle 3.3.1 incompatible | Use `paddlepaddle==3.0.0` |
| `IndexError: string index out of range` | Using old API format on PaddleOCR 3.x | Use `result[0]['rec_texts']` |
| Subprocess encoding issues on Windows | Paddle logs contain binary data | Use direct import, not subprocess |
| OCR hanging or crashing | Cached models from wrong version | `rm -rf ~/.paddlex/official_models/` |

## Singleton Pattern (Recommended)

```python
_ocr_instance = None

def _get_ocr(lang="ch"):
    global _ocr_instance
    if _ocr_instance is None:
        from paddleocr import PaddleOCR
        _ocr_instance = PaddleOCR(lang=lang)
    return _ocr_instance
```

This avoids re-initializing all 5 models on each call.
