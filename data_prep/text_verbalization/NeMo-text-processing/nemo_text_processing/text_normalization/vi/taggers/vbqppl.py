import pynini
from pynini.lib import pynutil

from nemo_text_processing.text_normalization.vi.graph_utils import NEMO_DIGIT, GraphFst


class VbqpplFst(GraphFst):
    """Classifies legal document identifiers like 146/2017/TT-BTC."""

    def __init__(self, deterministic: bool = True):
        super().__init__(name="vbqppl", kind="classify", deterministic=deterministic)

        uppercase = pynini.union(*list("ABCDEFGHIJKLMNOPQRSTUVWXYZĐ")).optimize()
        lowercase = pynini.union(*list("abcdefghijklmnopqrstuvwxyzđ")).optimize()
        alpha = (uppercase | lowercase).optimize()

        so = pynini.closure(NEMO_DIGIT, 1, 4)
        nam = pynini.closure(NEMO_DIGIT, 4, 4)
        loaivanban = pynini.closure(alpha, 1, 6)

        coquan_segment = pynini.closure(alpha, 2) + pynini.closure(NEMO_DIGIT)
        coquan = coquan_segment + pynini.closure(pynutil.delete("-") + pynutil.insert("-") + coquan_segment)

        graph = (
            pynutil.insert('so: "')
            + so
            + pynutil.insert('"')
            + pynutil.delete("/")
            + (
                pynutil.insert(' nam: "')
                + nam
                + pynutil.insert('"')
                + pynutil.delete("/")
            ).ques
            + (
                pynutil.insert(' loaivanban: "')
                + loaivanban
                + pynutil.insert('"')
                + pynutil.delete("-")
            ).ques
            + pynutil.insert(' coquan: "')
            + coquan
            + pynutil.insert('"')
        ).optimize()

        self.fst = self.add_tokens(graph).optimize()
