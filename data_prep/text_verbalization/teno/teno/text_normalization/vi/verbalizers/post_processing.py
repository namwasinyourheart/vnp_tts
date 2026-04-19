# Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from typing import Dict, List

import pynini
import regex
from pynini.lib import pynutil
from pynini.lib.rewrite import top_rewrite

from nemo_text_processing.text_normalization.vi.graph_utils import NEMO_SIGMA, NEMO_SPACE, generator_main
from nemo_text_processing.text_normalization.vi.utils import get_abs_path, load_labels
from nemo_text_processing.utils.logging import logger


class PostProcessingFst:
    """
    Finite state transducer that post-processes an entire Vietnamese sentence after verbalization is complete, e.g.
    removes extra spaces around punctuation marks " ( một trăm hai mươi ba ) " -> "(một trăm hai mươi ba)"

    Args:
        cache_dir: path to a dir with .far grammar file. Set to None to avoid using cache.
        overwrite_cache: set to True to overwrite .far files
    """

    def __init__(self, cache_dir: str = None, overwrite_cache: bool = False):

        far_file = None
        if cache_dir is not None and cache_dir != "None":
            os.makedirs(cache_dir, exist_ok=True)
            far_file = os.path.join(cache_dir, "vi_tn_post_processing.far")
        if not overwrite_cache and far_file and os.path.exists(far_file):
            self.fst = pynini.Far(far_file, mode="r")["post_process_graph"]
            logger.info(f'Post processing graph was restored from {far_file}.')
        else:
            self.set_punct_dict()
            self.fst = self.get_punct_postprocess_graph()

            if far_file:
                generator_main(far_file, {"post_process_graph": self.fst})

        self._symbol_replace_map = self._load_symbol_replace_map()

    def _load_symbol_replace_map(self) -> Dict[str, str]:
        symbol_path = get_abs_path("data/whitelist/symbol.txt")
        mapping: Dict[str, str] = {}
        try:
            with open(symbol_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if " | " not in line:
                        continue
                    sym, spoken = line.split(" | ", 1)
                    sym = sym.strip()
                    spoken = spoken.strip()
                    if not sym or not spoken:
                        continue
                    mapping[sym] = spoken
        except Exception:
            # Keep it safe: if file missing or malformed, just disable symbol replacement.
            mapping = {}
        return mapping

    def process(self, normalized_text: str) -> str:
        """Vietnamese post-processing for final text.

        This runs the WFST punctuation post-processing and then applies a conservative
        Python-level symbol replacement for leftover symbols.
        """

        if normalized_text is None:
            return normalized_text
        normalized_text = normalized_text.strip()
        if not normalized_text:
            return normalized_text

        debug_punct = os.getenv("NEMO_VI_DEBUG_PUNCT", "false").lower() == "true"
        pre_fst_text = normalized_text

        # top_rewrite handles the text directly with the FST.
        normalized_text = top_rewrite(normalized_text, self.fst)
        post_fst_text = normalized_text

        # Verbalize slash only in letter/letter contexts, e.g. "cơ sở/trẻ/tháng" -> "cơ sở trên trẻ/tháng".
        # We keep '/' out of symbol.txt to avoid global replacement.
        # Exclude URLs and absolute paths.
        if "://" not in normalized_text and not normalized_text.startswith("/"):
            normalized_text = regex.sub(r"(?<=\p{L})/(?=\p{L})", " trên ", normalized_text)
            # Also verbalize slash between digits as fraction separator: "2/9" -> "2 trên 9".
            normalized_text = regex.sub(r"(?<=\d)/(?=\d)", " trên ", normalized_text)
            # Handle tokenized spacing around '/': "2 / 9" -> "2 trên 9".
            normalized_text = regex.sub(r"(?<=\d)\s*/\s*(?=\d)", " trên ", normalized_text)

        # Replace leftover symbols in final string.
        for sym, spoken in self._symbol_replace_map.items():
            normalized_text = normalized_text.replace(sym, f" {spoken} ")

        # Collapse multiple spaces.
        while "  " in normalized_text:
            normalized_text = normalized_text.replace("  ", " ")

        # Option B support: if the input is an ambiguous numeric form like "2/9" and it was not
        # classified as a date (no explicit date context), it may survive as number words around '/'
        # after verbalization (e.g., "hai / chín"). Convert those to "hai trên chín" before
        # the generic separator-to-comma cleanup.
        number_words = (
            "không|một|hai|ba|bốn|tư|năm|sáu|bảy|tám|chín|mười"
        )
        normalized_text = regex.sub(
            rf"(?i)(?<!\p{{L}})({number_words})\s*/\s*({number_words})(?!\p{{L}})",
            r"\1 trên \2",
            normalized_text,
        )

        drop_symbols = {
            '"',
            "'",
            "“",
            "”",
            "„",
            "‟",
            "‘",
            "’",
            "‚",
            "‛",
            "`",
            "´",
        }
        for sym in drop_symbols:
            if sym in normalized_text:
                normalized_text = normalized_text.replace(sym, "")

        # Final cleanup: replace leftover separators such as '-' and '/' with comma pauses.
        # Keep standard punctuation (.,?!) intact by only rewriting these separators when they appear
        # between tokens (i.e., around whitespace) or as a trailing separator before whitespace.
        # Examples:
        #   "17- TB" -> "17, TB"
        #   "tê bê / u bê" -> "tê bê, u bê"
        import re
        # Slash surrounded by whitespace: " a / b " -> " a, b "
        # (Require whitespace so we don't touch numeric forms like "2/9" which are handled above.)
        normalized_text = re.sub(r"\s+/\s+", ", ", normalized_text)
        # Hyphen surrounded by whitespace: " a - b " -> " a, b "
        normalized_text = re.sub(r"\s+-\s+", ", ", normalized_text)
        # Hyphen trailing a number before whitespace: "17- TB" -> "17, TB"
        normalized_text = re.sub(r"(?<=\d)-(?=\s)", ",", normalized_text)
        # Normalize comma spacing and remove duplicates that could be introduced by the rules above.
        normalized_text = re.sub(r"\s*,\s*", ", ", normalized_text)
        normalized_text = re.sub(r"(,\s*){2,}", ", ", normalized_text)

        pre_punct_dedupe_text = normalized_text

        # Normalize sentence-ending punctuation to avoid duplicated periods like ".." or ". .".
        # normalized_text = re.sub(r"\s+([.!?])", r"\1", normalized_text)
        # normalized_text = re.sub(r"([.!?])(?:\s*\1)+", r"\1", normalized_text)

        if debug_punct and (".." in pre_punct_dedupe_text or ".." in post_fst_text or " .." in pre_punct_dedupe_text):
            logger.info("VI_PUNCT_DEBUG pre_fst=%r", pre_fst_text)
            logger.info("VI_PUNCT_DEBUG post_fst=%r", post_fst_text)
            logger.info("VI_PUNCT_DEBUG pre_dedupe=%r", pre_punct_dedupe_text)
            logger.info("VI_PUNCT_DEBUG post_dedupe=%r", normalized_text)

        # Final cleanup: collapse multiple spaces again after removing symbols
        while "  " in normalized_text:
            normalized_text = normalized_text.replace("  ", " ")

        return normalized_text.strip()

    def get_vietnamese_punct_config(self) -> Dict[str, List[str]]:
        """
        Returns Vietnamese-specific punctuation configuration.
        This method can be easily modified or extended for different Vietnamese punctuation rules.
        """
        return {
            # Punctuation that should not have space before them
            'no_space_before': [",", ".", "!", "?", ":", ";", ")", r"\]", "}"],
            # Punctuation that should not have space after them
            'no_space_after': ["(", r"\[", "{"],
            # Punctuation that can have space before them (exceptions)
            'allow_space_before': ["&", "-", "—", "–", "(", r"\[", "{", "\"", "'", "«", "»"],
            # Special Vietnamese punctuation handling
            'vietnamese_special': {
                # Vietnamese quotation marks
                'quotes': ["\"", "'", "«", "»", """, """, "'", "'"],
                # Vietnamese dashes and separators
                'dashes': ["-", "—", "–"],
                # Vietnamese brackets
                'brackets': ["(", ")", r"\[", r"\]", "{", "}"],
            },
        }

    def set_punct_dict(self):
        # Vietnamese punctuation marks that might need special handling
        self.punct_marks = {
            "'": [
                "'",
                '´',
                'ʹ',
                'ʻ',
                'ʼ',
                'ʽ',
                'ʾ',
                'ˈ',
                'ˊ',
                'ˋ',
                '˴',
                'ʹ',
                '΄',
                '`',
                '´',
                '’',
                '‛',
                '′',
                '‵',
                'ꞌ',
                '＇',
                '｀',
            ],
        }

    def get_punct_postprocess_graph(self):
        """
        Returns graph to post process punctuation marks for Vietnamese.

        Uses dynamic configuration for flexible punctuation handling.
        Vietnamese punctuation spacing rules are defined in get_vietnamese_punct_config().
        """
        # Get dynamic punctuation configuration
        punct_config = self.get_vietnamese_punct_config()

        # Extract configuration
        no_space_before_punct = punct_config['no_space_before']
        no_space_after_punct = punct_config['no_space_after']

        # Create FSTs for punctuation rules
        no_space_before_punct_fst = pynini.union(*no_space_before_punct)
        no_space_after_punct_fst = pynini.union(*no_space_after_punct)

        delete_space = pynutil.delete(NEMO_SPACE)

        # Rule 0: Verbalize leftover symbols in the final text.
        # We keep this conservative to avoid breaking URLs/paths, so we only rewrite a small set.
        symbol_labels = load_labels(get_abs_path("data/whitelist/symbol.tsv"))
        allowed_symbols = {"+", "&", "=", "%", "$", "₫", "×", "÷"}
        symbol_labels = [pair for pair in symbol_labels if pair and pair[0] in allowed_symbols]

        # Replace symbols when they appear as separate tokens: " a & b " -> " a và b ".
        # We preserve spaces around the inserted spoken form by emitting them in the replacement.
        symbol_token_rule = pynini.union(
            *[
                pynini.cdrewrite(
                    pynini.cross(sym, f" {spoken} "),
                    NEMO_SPACE,
                    NEMO_SPACE,
                    NEMO_SIGMA,
                )
                for sym, spoken in symbol_labels
            ]
        ).optimize()

        # Also handle glued digit cases like "1&2" after verbalization (rare, but happens in raw text).
        # We only handle digits here to keep the rule safe.
        digit = pynini.union(*"0123456789")
        glued_amp_rule = pynini.cdrewrite(pynini.cross("&", " và "), digit, digit, NEMO_SIGMA).optimize()
        glued_plus_rule = pynini.cdrewrite(pynini.cross("+", " cộng "), digit, digit, NEMO_SIGMA).optimize()

        # Rule 0.5: Collapse multiple spaces into a single space.
        # This removes artifacts like "  " introduced by conservative rewrites.
        multi_space = NEMO_SPACE + pynini.closure(NEMO_SPACE, 1)
        collapse_multi_space = pynini.cdrewrite(pynini.cross(multi_space, NEMO_SPACE), "", "", NEMO_SIGMA).optimize()

        # Rule 1: Remove space before punctuation (primary rule)
        remove_space_before = pynini.cdrewrite(
            delete_space + no_space_before_punct_fst,  # " ," -> ","
            "",  # any context before
            "",  # any context after
            NEMO_SIGMA,
        ).optimize()

        # Rule 2: Remove space after opening brackets
        remove_space_after = pynini.cdrewrite(
            no_space_after_punct_fst + delete_space, "", "", NEMO_SIGMA  # "( " -> "("
        ).optimize()

        # Combine post-processing rules
        graph = pynini.compose(symbol_token_rule, glued_amp_rule)
        graph = pynini.compose(graph, glued_plus_rule)
        graph = pynini.compose(graph, collapse_multi_space)
        graph = pynini.compose(graph, remove_space_before)
        graph = pynini.compose(graph, remove_space_after)

        return graph.optimize()
