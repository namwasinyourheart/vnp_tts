import pynini
from pynini.lib import pynutil

from nemo_text_processing.text_normalization.vi.graph_utils import GraphFst, convert_space
from nemo_text_processing.text_normalization.vi.utils import get_abs_path


def _load_abbreviation_labels(abs_path: str):
    labels = []
    with open(abs_path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue

            if " | " not in stripped:
                continue

            key, value = stripped.split(" | ", 1)

            key = key.strip()
            value = value.strip()
            if not key or not value:
                continue
            labels.append((key, value))
    return labels


def _load_letter_sounds(abs_path: str):
    labels = []
    with open(abs_path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if " | " not in stripped:
                continue
            key, value = stripped.split(" | ", 1)
            key = key.strip()
            value = value.strip()
            if key and value:
                labels.append((key, value))
    return labels


class AbbreviationFst(GraphFst):
    """Finite state transducer for Vietnamese abbreviation expansion."""

    def __init__(self, deterministic: bool = True):
        super().__init__(name="abbreviation", kind="classify", deterministic=deterministic)

        labels = _load_abbreviation_labels(get_abs_path("data/abbreviation/abbreviation.txt"))
        dict_graph = pynini.string_map(labels)

        letter_pairs = _load_letter_sounds(get_abs_path("data/alphanumeric_letter_sound_vn_iy.txt"))
        upper_letter_pairs = [(k.upper(), v) for k, v in letter_pairs]
        upper_letter = pynini.string_map(upper_letter_pairs).optimize()
        fallback_graph = upper_letter + pynini.closure(pynutil.insert(" ") + upper_letter, 1)
        fallback_graph = pynutil.add_weight(fallback_graph, 0.1)

        graph = (dict_graph | fallback_graph).optimize()

        self.graph = graph
        self.final_graph = convert_space(self.graph).optimize()
        self.fst = (pynutil.insert('value: "') + self.final_graph + pynutil.insert('"')).optimize()
        self.fst = self.add_tokens(self.fst)
