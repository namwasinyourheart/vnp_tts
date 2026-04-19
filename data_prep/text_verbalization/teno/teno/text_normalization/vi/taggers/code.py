import string

import pynini
from pynini.lib import pynutil

from nemo_text_processing.text_normalization.vi.graph_utils import (
    NEMO_ALPHA,
    NEMO_DIGIT,
    GraphFst,
    convert_space,
)
from nemo_text_processing.text_normalization.vi.utils import get_abs_path, load_labels


def _load_letter_sounds(abs_path: str):
    pairs = []
    with open(abs_path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if " | " not in stripped:
                continue
            src, dst = stripped.split(" | ", 1)
            src = src.strip()
            dst = dst.strip()
            if not src or not dst:
                continue

            if len(src) == 1 and src in string.ascii_lowercase:
                pairs.append((src, dst))
                pairs.append((src.upper(), dst))
            else:
                pairs.append((src, dst))
    return pairs


class CodeFst(GraphFst):
    """Classifies hyphenated codes, e.g. DH-2026-04-001, IPU-152."""

    def __init__(self, cardinal: GraphFst, deterministic: bool = True):
        super().__init__(name="code", kind="classify", deterministic=deterministic)

        letter_pairs = _load_letter_sounds(get_abs_path("data/alphanumeric_letter_sound_vn_iy.txt"))
        letter_unit = pynini.string_map(letter_pairs).optimize()
        letter_pairs_no_hour = [(k, v) for k, v in letter_pairs if k not in {"h", "H"}]
        letter_unit_no_hour = pynini.string_map(letter_pairs_no_hour).optimize()
        letter_seq = letter_unit + pynini.closure(pynutil.insert(" ") + letter_unit)
        letter_seq_no_hour = letter_unit_no_hour + pynini.closure(pynutil.insert(" ") + letter_unit_no_hour)

        digit_pairs = load_labels(get_abs_path("data/numbers/digit.tsv"))
        zero_pairs = load_labels(get_abs_path("data/numbers/zero.tsv"))
        digit_pairs = [*digit_pairs, *zero_pairs]
        digit_unit = pynini.string_map(digit_pairs).optimize()
        digit_seq_by_digit = digit_unit + pynini.closure(pynutil.insert(" ") + digit_unit)

        digit_seq = pynini.closure(NEMO_DIGIT, 1)
        leading_zero_multi = pynini.accep("0") + pynini.closure(NEMO_DIGIT, 1)
        leading_zero_spoken = pynutil.add_weight(leading_zero_multi @ digit_seq_by_digit, -0.1)
        number_seq = leading_zero_spoken | (digit_seq @ cardinal.graph)

        # Allow mixed segments such as "86B" or "B86" inside hyphenated codes.
        mixed_d_l = (digit_seq @ cardinal.graph) + pynutil.insert(" ") + letter_seq_no_hour
        mixed_l_d = letter_seq + pynutil.insert(" ") + number_seq
        segment = letter_seq | number_seq | mixed_d_l | mixed_l_d

        dash_segment = pynutil.delete("-") + pynutil.insert(", ") + segment
        # Also allow slash as delimiter (e.g., 17-TB/UBKT)
        # Output with " / " to allow post-processing to verbalize as "trên"
        slash_segment = pynutil.delete("/") + pynutil.insert(" / ") + segment
        delimiter_segment = pynutil.add_weight(dash_segment, -0.01) | pynutil.add_weight(slash_segment, -0.01)
        # Require at least one dash delimiter so slash-only patterns (e.g. 299792km/s)
        # are not stolen from the measure tagger.
        graph = segment + pynini.closure(delimiter_segment) + dash_segment + pynini.closure(delimiter_segment)

        self.graph = graph.optimize()
        self.final_graph = convert_space(self.graph).optimize()
        self.fst = (pynutil.insert('value: "') + self.final_graph + pynutil.insert('"')).optimize()
        self.fst = self.add_tokens(self.fst)
