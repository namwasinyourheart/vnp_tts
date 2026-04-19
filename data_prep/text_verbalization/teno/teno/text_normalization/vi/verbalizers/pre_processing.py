from __future__ import annotations

import re
import unicodedata


_DASH_CHARS = {
    "\u2010",  # hyphen
    "\u2011",  # non-breaking hyphen
    "\u2012",  # figure dash
    "\u2013",  # en dash
    "\u2014",  # em dash
    "\u2015",  # horizontal bar
    "\u2212",  # minus sign
    "\ufe58",  # small em dash
    "\ufe63",  # small hyphen-minus
    "\uff0d",  # fullwidth hyphen-minus
    "\u2043",  # hyphen bullet
    "\u00ad",  # soft hyphen
}


def pre_process_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)

    if any(ch in text for ch in _DASH_CHARS):
        for ch in _DASH_CHARS:
            if ch in text:
                text = text.replace(ch, "-")

    text = text.replace("\u00a0", " ")

    # text = re.sub(r"\s*-\s*", "-", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()
