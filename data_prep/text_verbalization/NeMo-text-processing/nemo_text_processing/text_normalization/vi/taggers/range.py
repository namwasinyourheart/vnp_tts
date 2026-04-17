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

from nemo_text_processing.text_normalization.vi.graph_utils import NEMO_DIGIT, NEMO_SPACE, GraphFst
from nemo_text_processing.text_normalization.vi.utils import get_abs_path, load_labels


class RangeFst(GraphFst):
    """
    Finite state transducer for classifying Vietnamese ranges with dash "-"
    Examples:
        10k-20k -> tokens { name: "mười nghìn đến hai mười nghìn" }
        10h-8h -> tokens { name: "mười giờ đến tám giờ" }
        10$-20$ -> tokens { name: "mười đô la đến hai mười đô la" }

    Args:
        time: composed time tagger and verbalizer
        date: composed date tagger and verbalizer
        decimal: composed decimal tagger and verbalizer
        money: composed money tagger and verbalizer
        deterministic: if True will provide a single transduction option,
            for False multiple transduction are generated (used for audio-based normalization)
    """

    def __init__(
        self,
        time: GraphFst,
        date: GraphFst,
        decimal: GraphFst,
        money: GraphFst,
        measure: GraphFst,
        cardinal: GraphFst,
        deterministic: bool = True,
    ):
        super().__init__(name="range", kind="classify", deterministic=deterministic)

        delete_space = pynini.closure(pynutil.delete(NEMO_SPACE), 0, 1)

        day_mappings = load_labels(get_abs_path("data/date/days.tsv"))
        month_mappings = load_labels(get_abs_path("data/date/months.tsv"))
        currency_major_labels = load_labels(get_abs_path("data/money/currency.tsv"))
        magnitude_labels = load_labels(get_abs_path("data/numbers/magnitudes.tsv"))

        one_or_two_digits = pynini.closure(NEMO_DIGIT, 1, 2)
        # Restrict years in range patterns to 4 digits to avoid ambiguities like "2-7/12"
        # being interpreted as a month range with year 12.
        year_digit = pynini.closure(NEMO_DIGIT, 4, 4)

        # Generic numeric for ranges like 20-30 (shared unit comes after the second number)
        range_number = pynini.closure(NEMO_DIGIT, 1, 6)
        range_number_words = pynini.compose(range_number, cardinal)

        day_convert = pynini.string_map([(k, v) for k, v in day_mappings])
        month_convert = pynini.string_map([(k, v) for k, v in month_mappings])
        year_convert = pynini.compose(year_digit, cardinal)

        currency_major_graph = pynini.string_map(currency_major_labels)
        quantity_units_keep = pynini.union(*[pynini.cross(v, v) for _, v in magnitude_labels])

        day_words = one_or_two_digits @ day_convert
        month_words = one_or_two_digits @ month_convert
        year_words = year_digit @ year_convert

        # Optional prefixes for Vietnamese range expressions.
        # We preserve the original casing in output.
        from_prefix = pynini.closure(
            pynini.union(
                *[
                    pynini.cross(v + NEMO_SPACE, f"{v} ")
                    for v in {"từ", "Từ", "TỪ"}
                ]
            ),
            0,
            1,
        )

        from_prefix_required = pynini.union(
            *[
                pynini.cross(v + NEMO_SPACE, f"{v} ")
                for v in {"từ", "Từ", "TỪ"}
            ]
        )

        context_prefix = pynini.closure(
            pynini.union(
                *[
                    pynini.cross(v + NEMO_SPACE, f"{v} ")
                    for v in {
                        "vào",
                        "Vào",
                        "VÀO",
                        "tại",
                        "Tại",
                        "TẠI",
                        "đến",
                        "Đến",
                        "ĐẾN",
                    }
                ]
            ),
            0,
            1,
        )

        # For "ngày" and "tháng" we accept them as optional input prefixes.
        # "ngày" is preserved only when present.
        day_prefix_keep = pynini.closure(pynini.cross("ngày" + NEMO_SPACE, "ngày "), 0, 1)
        day_prefix_emit = pynini.union(
            pynini.cross("ngày" + NEMO_SPACE, "ngày "),
            pynini.cross("Ngày" + NEMO_SPACE, "Ngày "),
            pynini.cross("NGÀY" + NEMO_SPACE, "NGÀY "),
            pynutil.insert("ngày "),
        )
        month_prefix_keep = pynini.closure(pynini.cross("tháng" + NEMO_SPACE, "tháng "), 0, 1)

        # Pattern: "<context> D/M và D/M" (date and date) without forcing bare "D/M và D/M".
        # This fixes cases like "ngày 7/4 và 8/4" while leaving "9/4 và 10/4" to fraction + date heuristics.
        ngay_prefix_required = pynini.union(
            pynini.cross("ngày" + NEMO_SPACE, "ngày "),
            pynini.cross("Ngày" + NEMO_SPACE, "Ngày "),
            pynini.cross("NGÀY" + NEMO_SPACE, "NGÀY "),
        )

        other_context_prefix_required = pynini.union(
            *[
                pynini.cross(v + NEMO_SPACE, f"{v} ")
                for v in {
                    "sáng",
                    "Sáng",
                    "SÁNG",
                    "trưa",
                    "Trưa",
                    "TRƯA",
                    "chiều",
                    "Chiều",
                    "CHIỀU",
                    "tối",
                    "Tối",
                    "TỐI",
                    "đêm",
                    "Đêm",
                    "ĐÊM",
                    "hôm",
                    "Hôm",
                    "HÔM",
                    "buổi",
                    "Buổi",
                    "BUỔI",
                    "bữa",
                    "Bữa",
                    "BỮA",
                    "lúc",
                    "Lúc",
                    "LÚC",
                    "từ",
                    "Từ",
                    "TỪ",
                    "đến",
                    "Đến",
                    "ĐẾN",
                    "vào",
                    "Vào",
                    "VÀO",
                    "tại",
                    "Tại",
                    "TẠI",
                    "trước",
                    "Trước",
                    "TRƯỚC",
                    "sau",
                    "Sau",
                    "SAU",
                }
            ]
        )
        # Conjunction "và". Keep it robust to spacing in input and normalize spacing in output.
        va_emit = pynini.union(
            pynini.cross("và", "và"),
            pynini.cross("Và", "Và"),
            pynini.cross("VÀ", "VÀ"),
        )

        thang_prefix_required = pynini.union(
            pynini.cross("tháng" + NEMO_SPACE, "tháng "),
            pynini.cross("Tháng" + NEMO_SPACE, "Tháng "),
            pynini.cross("THÁNG" + NEMO_SPACE, "THÁNG "),
        )

        day_month_spoken = (
            day_words
            + (pynutil.delete("/") | pynutil.delete("."))
            + pynutil.insert(" tháng ")
            + month_words
        )

        month_year_spoken = (
            month_words
            + (pynutil.delete("/") | pynutil.delete("."))
            + pynutil.insert(" năm ")
            + year_words
        )

        context_day_month_va_day_month = pynutil.add_weight(
            (
                (
                    # Explicit 'ngày' prefix: keep it as-is.
                    (ngay_prefix_required + day_month_spoken)
                    # Other temporal prefixes: insert 'ngày' for natural reading.
                    | (other_context_prefix_required + pynutil.insert("ngày ") + day_month_spoken)
                )
                + delete_space
                + pynutil.insert(" ")
                + va_emit
                + pynutil.insert(" ")
                + delete_space
                + pynutil.insert("ngày ")
                + day_month_spoken
            ),
            -3.0,
        )

        context_month_year_va_month_year = pynutil.add_weight(
            (
                (
                    # Explicit 'tháng' prefix: keep it as-is.
                    (thang_prefix_required + month_year_spoken)
                    # Other temporal prefixes: insert 'tháng' for natural reading.
                    | (other_context_prefix_required + pynutil.insert("tháng ") + month_year_spoken)
                )
                + delete_space
                + pynutil.insert(" ")
                + va_emit
                + pynutil.insert(" ")
                + delete_space
                + pynutil.insert("tháng ")
                + month_year_spoken
            ),
            -3.0,
        )

        # Abbreviated date ranges with shared month/year suffixes
        # Examples:
        #   từ ngày 14-17/4 -> từ ngày mười bốn đến mười bảy tháng tư
        #   từ ngày 14-17/4/2024 -> từ ngày mười bốn đến mười bảy tháng tư năm hai nghìn hai mươi tư
        #   từ 14-20.2.2018 -> từ mười bốn đến hai mươi tháng hai năm hai nghìn không trăm mười tám
        sep_day_month = pynini.union(pynini.accep("/"), pynini.accep("."))

        day_range_prefix = (from_prefix_required | from_prefix) + day_prefix_emit

        day_day_month = pynutil.add_weight(
            (
                day_range_prefix
                + day_words
                + delete_space
                + pynini.cross("-", " đến ngày ")
                + delete_space
                + day_words
                + pynutil.delete(sep_day_month)
                + pynutil.insert(" tháng ")
                + month_words
            ),
            -3.0,
        )

        # Full abbreviated date range where both sides include day/month.
        # Example: từ 24/1-6/2 -> từ ngày hai mươi bốn tháng một đến ngày sáu tháng hai
        day_month_day_month = pynutil.add_weight(
            (
                from_prefix
                + pynutil.insert("ngày ")
                + day_words
                + (
                    (pynutil.delete("/") + pynutil.insert(" tháng "))
                    | (pynutil.delete(".") + pynutil.insert(" tháng "))
                )
                + month_words
                + delete_space
                + pynini.cross("-", " đến ")
                + delete_space
                + pynutil.insert("ngày ")
                + day_words
                + (
                    (pynutil.delete("/") + pynutil.insert(" tháng "))
                    | (pynutil.delete(".") + pynutil.insert(" tháng "))
                )
                + month_words
            ),
            -3.5,
        )

        day_day_month_year = pynutil.add_weight(
            (
                day_range_prefix
                + day_words
                + delete_space
                + pynini.cross("-", " đến ngày ")
                + delete_space
                + day_words
                + (
                    (pynutil.delete("/") + pynutil.insert(" tháng ") + month_words + pynutil.delete("/") )
                    | (pynutil.delete(".") + pynutil.insert(" tháng ") + month_words + pynutil.delete("."))
                )
                + pynutil.insert(" năm ")
                + year_words
            ),
            -3.0,
        )

        # Abbreviated month ranges with shared year suffix
        # Example: Từ 4-5/2026 -> Từ tháng bốn đến tháng năm năm hai nghìn không trăm hai mươi sáu
        # Also accepts: từ tháng 4-5/2026
        month_prefix_delete = pynini.closure(
            pynini.union(
                pynutil.delete("tháng" + NEMO_SPACE),
                pynutil.delete("Tháng" + NEMO_SPACE),
                pynutil.delete("THÁNG" + NEMO_SPACE),
            ),
            0,
            1,
        )

        month_month_year = pynutil.add_weight(
            (
                (from_prefix | context_prefix)
                + month_prefix_delete
                + pynutil.insert("tháng ")
                + month_words
                + delete_space
                + pynini.cross("-", " đến ")
                + delete_space
                + pynutil.insert("tháng ")
                + month_words
                + (pynutil.delete("/") | pynutil.delete("."))
                + pynutil.insert(" năm ")
                + year_words
            ),
            -2.0,
        )

        specialized_range = (
            day_month_day_month
            | day_day_month_year
            | day_day_month
            | month_month_year
            | context_day_month_va_day_month
            | context_month_year_va_month_year
        )

        # Date-to-date ranges.
        # - Bare form keeps dash (e.g., 24/6/1967 - 24/6/2017).
        # - With explicit "từ" prefix uses "đến".
        date_range_with_from = pynutil.add_weight(
            (
                from_prefix_required
                + date
                + delete_space
                + pynini.cross("-", " đến ")
                + delete_space
                + date
            ),
            -3.0,
        )

        date_range_bare = pynutil.add_weight(
            (
                date
                + delete_space
                + pynini.cross("-", " - ")
                + delete_space
                + date
            ),
            -3.0,
        )

        specialized_range |= date_range_with_from | date_range_bare

        # Numeric range with shared measure unit on the right.
        # Example: từ 20-30 độ -> từ hai mươi đến ba mươi độ
        numeric_measure_range = pynutil.add_weight(
            (
                from_prefix
                + range_number_words
                + delete_space
                + pynini.cross("-", " đến ")
                + delete_space
                + measure
            ),
            -2.0,
        )

        # Numeric range with shared money unit on the right.
        # Example: 7-8 triệu đồng -> bảy đến tám triệu đồng
        numeric_money_range = pynutil.add_weight(
            (
                from_prefix
                + range_number_words
                + delete_space
                + pynini.cross("-", " đến ")
                + delete_space
                + range_number_words
                + delete_space
                + (pynutil.insert(" ") + quantity_units_keep).ques
                + delete_space
                + pynutil.insert(" ")
                + currency_major_graph
            ),
            -2.0,
        )

        # Plain numeric ranges.
        # Examples:
        #   7-8 -> bảy đến tám
        #   từ 7-10 -> từ bảy đến mười
        numeric_plain_range = pynutil.add_weight(
            (
                from_prefix
                + range_number_words
                + delete_space
                + pynini.cross("-", " đến ")
                + delete_space
                + range_number_words
            ),
            -2.0,
        )

        # Numeric ranges with Vietnamese quantity suffix on the right.
        # Examples:
        #   7-8 triệu -> bảy đến tám triệu
        #   7-8 tỷ -> bảy đến tám tỷ
        #   7-8 nghìn -> bảy đến tám nghìn
        numeric_quantity_range = pynutil.add_weight(
            (
                numeric_plain_range
                + delete_space
                + pynutil.insert(" ")
                + quantity_units_keep
            ),
            -2.0,
        )

        # Numeric ranges with common count nouns.
        # Example: 7-8 chiếc -> bảy đến tám chiếc
        count_noun_keep = pynini.union(
            pynini.cross("chiếc", "chiếc"),
            pynini.cross("Chiếc", "Chiếc"),
            pynini.cross("CHIẾC", "CHIẾC"),
        )
        numeric_count_noun_range = pynutil.add_weight(
            (
                numeric_plain_range
                + delete_space
                + pynutil.insert(" ")
                + count_noun_keep
            ),
            -2.0,
        )

        # Pattern: X-Y -> X đến Y
        # This will handle time ranges, date ranges, decimal ranges, and money ranges with dash
        range_pattern = (
            (time | date | decimal | money | measure)
            + delete_space
            + pynini.cross("-", " đến ")
            + delete_space
            + (time | date | decimal | money | measure)
        )

        self.graph = (
            specialized_range
            | numeric_measure_range
            | numeric_money_range
            | numeric_quantity_range
            | numeric_count_noun_range
            | numeric_plain_range
            | range_pattern
        )

        # Convert to final FST format
        self.graph = self.graph.optimize()
        graph = pynutil.insert("name: \"") + self.graph + pynutil.insert("\"")
        self.fst = graph.optimize()
