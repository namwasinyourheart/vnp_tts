import pynini
from pynini.lib import pynutil

from nemo_text_processing.text_normalization.vi.graph_utils import NEMO_DIGIT, GraphFst, delete_space
from nemo_text_processing.text_normalization.vi.taggers.cardinal import CardinalFst as TCardinalFst
from nemo_text_processing.text_normalization.vi.utils import get_abs_path


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
            if src and dst:
                pairs.append((src.upper(), dst))
                pairs.append((src.lower(), dst))
    return pairs


class VbqpplFst(GraphFst):
    """Verbalizes legal document identifiers into spoken Vietnamese."""

    def __init__(self, deterministic: bool = True):
        super().__init__(name="vbqppl", kind="verbalize", deterministic=deterministic)

        cardinal = TCardinalFst(deterministic=deterministic)
        cardinal_graph = cardinal.graph

        letter_pairs = _load_letter_sounds(get_abs_path("data/alphanumeric_letter_sound_vn_iy.txt"))
        letter_unit = pynini.string_map(letter_pairs).optimize()
        letter_seq = letter_unit + pynini.closure(pynutil.insert(" ") + letter_unit)

        digit_unit = pynini.string_file(get_abs_path("data/numbers/digit.tsv"))
        zero_unit = pynini.string_file(get_abs_path("data/numbers/zero.tsv"))
        digit_word = (digit_unit | zero_unit).optimize()
        digit_seq = digit_word + pynini.closure(pynutil.insert(" ") + digit_word)

        digits = pynini.closure(NEMO_DIGIT, 1)
        trimmed_leading_zero_digits = pynini.closure(pynutil.delete("0"), 1) + pynini.closure(NEMO_DIGIT, 1)
        spoken_digits = (digits @ cardinal_graph) | (trimmed_leading_zero_digits @ cardinal_graph)

        digits_with_leading_zero = pynini.accep("0") + pynini.closure(NEMO_DIGIT, 1)
        spoken_so_digits = (pynini.closure(NEMO_DIGIT, 1, 4) @ cardinal_graph) | (digits_with_leading_zero @ digit_seq)
        segment = letter_seq + (pynutil.insert(" ") + spoken_digits).ques
        abbreviation = segment + pynini.closure(pynutil.delete("-") + pynutil.insert(", ") + segment)

        so = pynutil.delete('so: "') + spoken_so_digits + pynutil.delete('"')
        nam = (
            delete_space
            + pynutil.delete('nam: "')
            + (pynini.closure(NEMO_DIGIT, 4, 4) @ cardinal_graph)
            + pynutil.delete('"')
        ).ques
        loaivanban = (
            delete_space
            + pynutil.delete('loaivanban: "')
            + abbreviation
            + pynutil.delete('"')
        ).ques
        coquan = (
            delete_space
            + pynutil.delete('coquan: "')
            + abbreviation
            + pynutil.delete('"')
        )

        graph = (
            so
            + (pynutil.insert(", ") + nam).ques
            + pynutil.insert(", ")
            + (loaivanban + pynutil.insert(", ")).ques
            + coquan
        )

        self.fst = self.delete_tokens(graph).optimize()
