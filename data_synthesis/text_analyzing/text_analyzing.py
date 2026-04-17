import re
from typing import List, Dict
from underthesea import word_tokenize

try:
    from vnp_tts.data_prep.text_verbalization.datetime_my import DATE_FULL_RE, DATE_DM_RE, DATE_MY_RE
except Exception:
    DATE_FULL_RE = re.compile(r"(?i)\b([0-3]?\d)\s*[\/\-.]\s*([01]?\d)\s*[\/\-.]\s*([12]\d{3})\b")
    DATE_DM_RE = re.compile(r"(?i)\b([0-3]?\d)\s*[\/\-.]\s*([01]?\d)\b(?![\/\-.]\s*\d)")
    DATE_MY_RE = re.compile(r"(?i)\b([01]?\d)\s*[\/\-.]\s*([12]\d{3})\b")

class TextAnalyzer:
    def __init__(self, language="vi"):
        self.language = language

    # 1. Preprocess text
    def preprocess_text(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        text = text.replace("–", "-").replace("—", "-")  # Replace em and en dash with hyphen
        return text

    # 2. Tokenize
    def tokenize(self, text: str):
        return word_tokenize(text)

    # 3. Sentence type
    def get_sentence_type(self, text: str) -> str:
        if text.endswith("?"):
            return "question"
        elif text.endswith("!"):
            return "exclamation"
        return "statement"

    # 4. Extract punctuation
    def extract_punctuation(self, text: str, punctuations=None):
        if punctuations is None:
            punctuations = [".", "?", "!", ",", ";", ":"]
        
        pattern = "[" + re.escape("".join(punctuations)) + "]"
        return re.findall(pattern, text)


    # 5. Extract special symbols
    def extract_special_symbols(self, text: str, exclude=None):
        """
        Extract all special symbols from text.
        
        :param text: input string
        :param exclude: list of characters to exclude (e.g., punctuation if you already handled them)
        """
        if exclude is None:
            exclude = []
        
        # Match anything that is NOT a-z, A-Z, 0-9 or whitespace
        pattern = r"[^a-zA-Z0-9\sÀ-ỹ]"
        
        symbols = re.findall(pattern, text)
        
        if exclude:
            symbols = [s for s in symbols if s not in exclude]

        symbols = set(symbols)
        
        return symbols

    def extract_dates(self, text: str) -> List[Dict]:
        results: List[Dict] = []

        def overlaps(start: int, end: int) -> bool:
            return any((start < r["end"] and end > r["start"]) for r in results)

        # Prefer full date > day/month > month/year to minimize ambiguity and overlap.
        for match in DATE_FULL_RE.finditer(text):
            d_s, m_s, y_s = match.groups()
            d, mo, y = int(d_s), int(m_s), int(y_s)
            if not (1 <= d <= 31 and 1 <= mo <= 12 and y > 0):
                continue
            if overlaps(match.start(), match.end()):
                continue
            results.append({
                "text": match.group(),
                "type": "date_full",
                "start": match.start(),
                "end": match.end(),
                "components": {"day": d, "month": mo, "year": y},
            })

        for match in DATE_DM_RE.finditer(text):
            d_s, m_s = match.groups()
            d, mo = int(d_s), int(m_s)
            if not (1 <= d <= 31 and 1 <= mo <= 12):
                continue
            if overlaps(match.start(), match.end()):
                continue
            results.append({
                "text": match.group(),
                "type": "date_dm",
                "start": match.start(),
                "end": match.end(),
                "components": {"day": d, "month": mo, "year": None},
            })

        for match in DATE_MY_RE.finditer(text):
            m_s, y_s = match.groups()
            mo, y = int(m_s), int(y_s)
            if not (1 <= mo <= 12 and y > 0):
                continue
            if overlaps(match.start(), match.end()):
                continue
            results.append({
                "text": match.group(),
                "type": "date_my",
                "start": match.start(),
                "end": match.end(),
                "components": {"day": None, "month": mo, "year": y},
            })

        results = sorted(results, key=lambda x: x["start"])
        return results

    def detect_dates(self, text: str) -> List[str]:
        normalized = self.preprocess_text(text)
        return detect_dates_nemo_text(normalized)

    # 5. Length features
    def get_length_features(self, text: str):
        words = text.split()
        return {
            "num_chars": len(text),
            "num_words": len(words)
        }

    # 6. Main pipeline
    def analyze(self, text: str) -> dict:
        normalized = self.preprocess_text(text)
        tokens = self.tokenize(normalized)
        sentence_type = self.get_sentence_type(normalized)
        punctuation = self.extract_punctuation(normalized)
        length = self.get_length_features(normalized)
        special_symbols = self.extract_special_symbols(normalized)

        return {
            "raw_text": text,
            "normalized_text": normalized,
            "tokens": tokens,
            "sentence_type": sentence_type,
            "punctuation": punctuation,
            "special_symbols": special_symbols,
            **length
        }


    COMMON_ABBREVIATIONS = {
        "TP.HCM": "Thành phố Hồ Chí Minh",
        "GS.": "Giáo sư",
        "TS.": "Tiến sĩ",
        "ThS.": "Thạc sĩ",
        "PGS.": "Phó giáo sư",
        "Dr.": "Doctor"
    }

    
    def extract_abbreviations(self, text: str) -> List[Dict]:
        results = []

        # ---- 1. Dot abbreviations (TP.HCM, GS., ThS.) ----
        dot_pattern = re.compile(r"\b(?:[A-Za-zĐđ]{1,5}\.){1,}[A-Za-zĐđ]{0,5}\b")

        for match in dot_pattern.finditer(text):
            abbr = match.group()

            results.append({
                "text": abbr,
                "type": "dot_abbreviation",
                "start": match.start(),
                "end": match.end(),
                "normalized": self.COMMON_ABBREVIATIONS.get(abbr)
            })

        # ---- 2. Hyphen abbreviations (NEW) ----
        hyphen_pattern = re.compile(r"\b[A-ZĐ]{1,5}(?:-[A-Za-zĐđ]{1,5})+\b")

        for match in hyphen_pattern.finditer(text):
            abbr = match.group()

            # skip overlap
            if any(r["start"] <= match.start() < r["end"] for r in results):
                continue

            results.append({
                "text": abbr,
                "type": "hyphen_abbreviation",
                "start": match.start(),
                "end": match.end(),
                "normalized": self.COMMON_ABBREVIATIONS.get(abbr)
            })


        # ---- 3. Uppercase abbreviations (USA, GDP, AI) ----
        upper_pattern = re.compile(r"\b[A-ZĐ]{2,}\b")

        for match in upper_pattern.finditer(text):
            abbr = match.group()

            # ❌ skip nếu đã nằm trong dot_abbreviation
            if any(r["start"] <= match.start() < r["end"] for r in results):
                continue

            # ❌ skip nếu là đầu câu (giảm false positive)
            if match.start() == 0:
                continue

            results.append({
                "text": abbr,
                "type": "uppercase_abbreviation",
                "start": match.start(),
                "end": match.end(),
                "normalized": self.COMMON_ABBREVIATIONS.get(abbr)
            })

        # ---- 3. Deduplicate + sort ----
        results = sorted(results, key=lambda x: x["start"])

        return results

    def analyze(
        self, 
        text: str, 
        features: list = None
    ) -> dict:
        
        if features is None:
            features = ["basic"]

        normalized = self.normalize(text)
        # tokens = self.tokenize(normalized)

        result = {
            "raw_text": text,
            "normalized_text": normalized,
            # "tokens": tokens,
        }

        if "sentence" in features:
            result["sentence_type"] = self.get_sentence_type(normalized)

        if "punctuation" in features:
            result["punctuation"] = self.extract_punctuation(normalized)

        if "length" in features:
            result.update(self.get_length_features(normalized))
        
        if "abbreviation" in features:
            result["abbreviation"] = self.extract_abbreviations(normalized)
        
        if "special_symbols" in features:
            result["special_symbols"] = self.extract_special_symbols(normalized)

        if "date" in features:
            result["date"] = self.extract_dates(normalized)

        return result


from dataclasses import dataclass, field
from typing import List


@dataclass
class TextFeatures:
    # raw
    raw_text: str
    
    # normalized
    # normalized_text: str
    
    # tokens
    tokens: List[str] = field(default_factory=list)
    
    # sentence-level features
    sentence_type: str = "statement"   # statement | question | exclamation
    punctuation: List[str] = field(default_factory=list)
    
    # length features
    num_chars: int = 0
    num_words: int = 0

    # optional (future extension)
    # pos_tags: List[str] = field(default_factory=list)
    # phonemes: List[str] = field(default_factory=list)
    # prosody: dict = field(default_factory=dict)

    # ---- helper methods ----
    def to_dict(self):
        return self.__dict__

    def __repr__(self):
        return f"TextFeatures(tokens={self.tokens}, type={self.sentence_type})"


def detect_dates_text(text: str) -> List[str]:
    analyzer = TextAnalyzer()
    normalized = analyzer.normalize(text)
    return [m["text"] for m in analyzer.extract_dates(normalized)]


_NEMO_DATE_SEP = r"[\/\-.]"
_NEMO_SP = r"\s+"
_NEMO_D1_2 = r"(?:0?[1-9]|[12]\d|3[01])"
_NEMO_M1_2 = r"(?:0?[1-9]|1[0-2])"
_NEMO_Y1_4 = r"\d{1,4}"


_NEMO_DATE_DAY_MONTH_YEAR_RE = re.compile(
    rf"(?:^|(?<!\w))ngày{_NEMO_SP}{_NEMO_D1_2}{_NEMO_SP}tháng{_NEMO_SP}{_NEMO_M1_2}{_NEMO_SP}năm{_NEMO_SP}{_NEMO_Y1_4}(?!\d)",
    re.IGNORECASE,
)
_NEMO_DATE_DDMMYYYY_RE = re.compile(
    rf"(?<!\d)(?:ngày{_NEMO_SP})?{_NEMO_D1_2}\s*{_NEMO_DATE_SEP}\s*{_NEMO_M1_2}\s*{_NEMO_DATE_SEP}\s*{_NEMO_Y1_4}(?!\d)",
    re.IGNORECASE,
)
_NEMO_DATE_YYYYMMDD_RE = re.compile(
    rf"(?<!\d){_NEMO_Y1_4}\s*{_NEMO_DATE_SEP}\s*{_NEMO_M1_2}\s*{_NEMO_DATE_SEP}\s*{_NEMO_D1_2}(?!\d)",
    re.IGNORECASE,
)
_NEMO_DATE_MONTH_YEAR_RE = re.compile(
    rf"(?:^|(?<!\w))tháng{_NEMO_SP}{_NEMO_M1_2}(?:{_NEMO_SP}|{_NEMO_DATE_SEP}){_NEMO_Y1_4}(?!\d)",
    re.IGNORECASE,
)
_NEMO_DATE_DAY_MONTH_RE = re.compile(
    rf"(?:^|(?<!\w))ngày{_NEMO_SP}{_NEMO_D1_2}(?:\s*{_NEMO_DATE_SEP}\s*{_NEMO_M1_2}|{_NEMO_SP}tháng{_NEMO_SP}{_NEMO_M1_2})(?!\d)",
    re.IGNORECASE,
)
_NEMO_DATE_YEAR_ONLY_RE = re.compile(
    rf"(?:^|(?<!\w))năm{_NEMO_SP}{_NEMO_Y1_4}(?!\d)",
    re.IGNORECASE,
)


def detect_dates_nemo_text(text: str) -> List[str]:
    patterns = [
        _NEMO_DATE_DAY_MONTH_YEAR_RE,
        _NEMO_DATE_DDMMYYYY_RE,
        _NEMO_DATE_YYYYMMDD_RE,
        _NEMO_DATE_MONTH_YEAR_RE,
        _NEMO_DATE_DAY_MONTH_RE,
        _NEMO_DATE_YEAR_ONLY_RE,
    ]

    matches = []
    for pat in patterns:
        for m in pat.finditer(text):
            matches.append((m.start(), m.end(), m.group(0)))

    matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))

    out: List[str] = []
    last_end = -1
    for start, end, s in matches:
        if start < last_end:
            continue
        out.append(s)
        last_end = end

    return out