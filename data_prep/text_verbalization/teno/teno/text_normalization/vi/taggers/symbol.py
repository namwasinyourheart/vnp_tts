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

import pynini
from pynini.lib import pynutil

from nemo_text_processing.text_normalization.vi.graph_utils import GraphFst, convert_space
from nemo_text_processing.text_normalization.vi.utils import get_abs_path, load_labels


class SymbolFst(GraphFst):
    """
    Finite state transducer for classifying symbols for Vietnamese, e.g.
        "+" -> tokens { name: "cộng" }
        "=" -> tokens { name: "bằng" }
        "%" -> tokens { name: "phần trăm" }
        "&" -> tokens { name: "và" }
        "$" -> tokens { name: "đô la" }
        "₫" -> tokens { name: "đồng" }
    This class has high priority to override other classifiers. Symbols are loaded from "data/whitelist/symbol.tsv".

    Args:
        input_case: accepting either "lower_cased" or "cased" input.
        deterministic: if True will provide a single transduction option,
            for False multiple options (used for audio-based normalization)
    """

    def __init__(self, input_case: str, deterministic: bool = True):
        super().__init__(name="symbol", kind="classify", deterministic=deterministic)

        def _get_symbol_graph(input_case, file):
            symbols = load_labels(file)
            if input_case == "lower_cased":
                symbols = [[x[0].lower()] + x[1:] for x in symbols]
            graph = pynini.string_map(symbols)
            return graph

        graph = _get_symbol_graph(input_case, get_abs_path("data/whitelist/symbol.tsv"))
        if not deterministic and input_case != "lower_cased":
            graph |= pynutil.add_weight(
                _get_symbol_graph("lower_cased", get_abs_path("data/whitelist/symbol.tsv")), weight=0.0001
            )

        self.graph = graph
        self.final_graph = convert_space(self.graph).optimize()
        self.fst = (pynutil.insert("name: \"") + self.final_graph + pynutil.insert("\"")).optimize()

        # Add tokens wrapper
        self.fst = self.add_tokens(self.fst)
