import pynini
from pynini.lib import pynutil

from nemo_text_processing.text_normalization.vi.graph_utils import (
    NEMO_NOT_QUOTE,
    NEMO_SIGMA,
    NEMO_SPACE,
    GraphFst,
    delete_space,
)


class CodeFst(GraphFst):
    """Verbalizes code tokens from `value` field."""

    def __init__(self, deterministic: bool = True):
        super().__init__(name="code", kind="verbalize", deterministic=deterministic)

        graph = (
            pynutil.delete("value:")
            + delete_space
            + pynutil.delete('"')
            + pynini.closure(NEMO_NOT_QUOTE, 1)
            + pynutil.delete('"')
        )
        graph = graph @ pynini.cdrewrite(pynini.cross("\u00a0", NEMO_SPACE), "", "", NEMO_SIGMA)
        self.fst = self.delete_tokens(graph).optimize()
