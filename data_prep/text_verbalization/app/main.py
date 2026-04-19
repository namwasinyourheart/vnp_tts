from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

APP_DIR = Path(__file__).resolve().parent
TEXT_VERBALIZATION_ROOT = APP_DIR.parent
TENO_ROOT = TEXT_VERBALIZATION_ROOT / "teno"
TENO_CACHE_DIR = Path(os.getenv("TENO_CACHE_DIR", APP_DIR / ".teno_cache"))
TENO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

if str(TENO_ROOT) not in sys.path:
    sys.path.insert(0, str(TENO_ROOT))

import teno as teno_pkg  # noqa: E402

sys.modules.setdefault("nemo_text_processing", teno_pkg)

from teno.text_normalization.normalize import Normalizer  # noqa: E402


class TextVerbalizationRequest(BaseModel):
    text: str = Field(..., description="Input text to normalize")
    lang: str = Field(default="vi", description="Language code, default: vi")


class BatchTextVerbalizationRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1, description="Input texts to normalize")
    lang: str = Field(default="vi", description="Language code, default: vi")


class TextVerbalizationResponse(BaseModel):
    normalized_text: str


class BatchTextVerbalizationResponse(BaseModel):
    normalized_texts: List[str]


@lru_cache(maxsize=8)
def get_normalizer(lang: str) -> Normalizer:
    return Normalizer(
        input_case=os.getenv("TENO_INPUT_CASE", "cased"),
        lang=lang,
        cache_dir=str(TENO_CACHE_DIR),
        overwrite_cache=os.getenv("TENO_OVERWRITE_CACHE", "false").lower() == "true",
    )


app = FastAPI(title="Text Verbalization API", version="1.0.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/text-verbalization", response_model=TextVerbalizationResponse)
def text_verbalization(payload: TextVerbalizationRequest) -> TextVerbalizationResponse:
    try:
        normalizer = get_normalizer(payload.lang)
        output = normalizer.normalize(payload.text)
        return TextVerbalizationResponse(normalized_text=output)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Normalization failed: {exc}") from exc


@app.post("/text-verbalization/batch", response_model=BatchTextVerbalizationResponse)
def text_verbalization_batch(payload: BatchTextVerbalizationRequest) -> BatchTextVerbalizationResponse:
    try:
        normalizer = get_normalizer(payload.lang)
        try:
            outputs = normalizer.normalize_list(payload.texts)
        except Exception:
            outputs = [normalizer.normalize(text) for text in payload.texts]
        return BatchTextVerbalizationResponse(normalized_texts=outputs)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Batch normalization failed: {exc}") from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)


# rm -rf /home/nampv1/projects/tts/vnp_tts/data_prep/text_verbalization/app/.teno_cache