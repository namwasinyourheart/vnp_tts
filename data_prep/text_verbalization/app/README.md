# Text Verbalization API

FastAPI service for Vietnamese text normalization (text verbalization), backed by NeMo text normalization rules in this repo.

## Workdir

`/home/nampv1/projects/tts/vnp_tts/data_prep/text_verbalization/app`

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Endpoints

- `GET /health`
- `POST /text-verbalization`
- `POST /text-verbalization/batch`

### Single

Request:

```json
{
  "text": "2A, K12, NTPA, 20H45",
  "lang": "vi"
}
```

Response:

```json
{
  "normalized_text": "hai a, ca mười hai, nờ tê pê a, hai mươi giờ bốn mươi lăm phút"
}
```

### Batch

Request:

```json
{
  "texts": [
    "Km153+450 và Km156+985",
    "ngày 20/1",
    "7h45"
  ],
  "lang": "vi"
}
```

Response:

```json
{
  "normalized_texts": [
    "ki lô mét một trăm năm mươi ba + bốn trăm năm mươi và ki lô mét một trăm năm mươi sáu + chín trăm tám mươi lăm",
    "ngày hai mươi tháng một",
    "bảy giờ bốn mươi lăm phút"
  ]
}
```

## Optional env vars

- `NEMO_CACHE_DIR`: custom cache directory (default: `./.nemo_cache`)
- `NEMO_INPUT_CASE`: `cased` (default) or other supported mode
- `NEMO_OVERWRITE_CACHE`: `true`/`false` (default: `false`)
