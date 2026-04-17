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


class DateFst(GraphFst):
    """
    Finite state transducer for classifying Vietnamese dates, e.g.
        15/01/2024 -> date { day: "mười lăm" month: "một" year: "hai nghìn hai mươi tư" }
        tháng 4 2024 -> date { month: "tư" year: "hai nghìn hai mươi tư" }
        ngày 15/01/2024 -> date { day: "mười lăm" month: "một" year: "hai nghìn hai mươi tư" }
        ngày 12 tháng 5 năm 2025 -> date { day: "mười hai" month: "năm" year: "hai nghìn hai mươi lăm" }
        năm 20 SCN -> date { year: "hai mươi" era: "sau công nguyên" }
    """

    def __init__(self, cardinal, deterministic: bool = True):
        super().__init__(name="date", kind="classify", deterministic=deterministic)

        # Vietnamese date keywords
        DAY_WORD = "ngày"
        MONTH_WORD = "tháng"
        YEAR_WORD = "năm"
        QUARTER_WORD = "quý"
        ORDINAL_YEAR_WORD = "năm thứ"

        # Prebuilt patterns for common usage
        day_prefix = pynini.union(
            pynini.accep(DAY_WORD + NEMO_SPACE),
            pynini.accep(DAY_WORD.capitalize() + NEMO_SPACE),
            pynini.accep(DAY_WORD.upper() + NEMO_SPACE),
        )
        day_prefix_keep = pynini.union(
            pynini.cross(DAY_WORD + NEMO_SPACE, 'day_prefix: "ngày" '),
            pynini.cross(DAY_WORD.capitalize() + NEMO_SPACE, 'day_prefix: "Ngày" '),
            pynini.cross(DAY_WORD.upper() + NEMO_SPACE, 'day_prefix: "NGÀY" '),
        )
        month_prefix = pynini.union(
            pynini.accep(MONTH_WORD + NEMO_SPACE),
            pynini.accep(MONTH_WORD.capitalize() + NEMO_SPACE),
            pynini.accep(MONTH_WORD.upper() + NEMO_SPACE),
        )
        month_prefix_keep = pynini.union(
            pynini.cross(MONTH_WORD + NEMO_SPACE, 'month_prefix: "tháng" '),
            pynini.cross(MONTH_WORD.capitalize() + NEMO_SPACE, 'month_prefix: "Tháng" '),
            pynini.cross(MONTH_WORD.upper() + NEMO_SPACE, 'month_prefix: "THÁNG" '),
        )
        year_prefix = pynini.union(
            pynini.accep(YEAR_WORD + NEMO_SPACE),
            pynini.accep(YEAR_WORD.capitalize() + NEMO_SPACE),
            pynini.accep(YEAR_WORD.upper() + NEMO_SPACE),
        )
        year_prefix_keep = pynini.union(
            pynini.cross(YEAR_WORD + NEMO_SPACE, 'year_prefix: "năm" '),
            pynini.cross(YEAR_WORD.capitalize() + NEMO_SPACE, 'year_prefix: "Năm" '),
            pynini.cross(YEAR_WORD.upper() + NEMO_SPACE, 'year_prefix: "NĂM" '),
        )
        quarter_prefix = pynini.union(
            pynini.accep(QUARTER_WORD + NEMO_SPACE),
            pynini.accep(QUARTER_WORD.capitalize() + NEMO_SPACE),
            pynini.accep(QUARTER_WORD.upper() + NEMO_SPACE),
        )
        quarter_prefix_keep = pynini.union(
            pynini.cross(QUARTER_WORD + NEMO_SPACE, 'quarter_prefix: "quý" '),
            pynini.cross(QUARTER_WORD.capitalize() + NEMO_SPACE, 'quarter_prefix: "Quý" '),
            pynini.cross(QUARTER_WORD.upper() + NEMO_SPACE, 'quarter_prefix: "QUÝ" '),
        )
        ordinal_year_prefix = pynini.union(
            pynini.accep(ORDINAL_YEAR_WORD + NEMO_SPACE),
            pynini.accep(ORDINAL_YEAR_WORD.capitalize() + NEMO_SPACE),
            pynini.accep(ORDINAL_YEAR_WORD.upper() + NEMO_SPACE),
        )
        ordinal_year_prefix_keep = pynini.union(
            pynini.cross(ORDINAL_YEAR_WORD + NEMO_SPACE, 'ordinal_year_prefix: "năm thứ" '),
            pynini.cross(ORDINAL_YEAR_WORD.capitalize() + NEMO_SPACE, 'ordinal_year_prefix: "Năm thứ" '),
            pynini.cross(ORDINAL_YEAR_WORD.upper() + NEMO_SPACE, 'ordinal_year_prefix: "NĂM THỨ" '),
        )

        context_prefix_words = [
            "sáng",
            "trưa",
            "chiều",
            "tối",
            "đêm",
            "hôm",
            "buổi",
            "bữa",
            "lúc",
            "từ",
            "đến",
            "vào",
            "tại",
            "trước",
            "sau"
        ]
        context_prefix = pynini.union(
            *[
                pynini.cross(
                    v + NEMO_SPACE,
                    f'prefix: "{v}" ',
                )
                for w in context_prefix_words
                for v in {w, w.capitalize(), w.upper()}
            ]
        ).optimize()

        delete_day_prefix = pynini.union(
            pynutil.delete(DAY_WORD + NEMO_SPACE),
            pynutil.delete(DAY_WORD.capitalize() + NEMO_SPACE),
            pynutil.delete(DAY_WORD.upper() + NEMO_SPACE),
        )
        delete_month_prefix = pynini.union(
            pynutil.delete(MONTH_WORD + NEMO_SPACE),
            pynutil.delete(MONTH_WORD.capitalize() + NEMO_SPACE),
            pynutil.delete(MONTH_WORD.upper() + NEMO_SPACE),
        )
        delete_year_prefix = pynini.union(
            pynutil.delete(YEAR_WORD + NEMO_SPACE),
            pynutil.delete(YEAR_WORD.capitalize() + NEMO_SPACE),
            pynutil.delete(YEAR_WORD.upper() + NEMO_SPACE),
        )
        delete_ordinal_year_prefix = pynini.union(
            pynutil.delete(ORDINAL_YEAR_WORD + NEMO_SPACE),
            pynutil.delete(ORDINAL_YEAR_WORD.capitalize() + NEMO_SPACE),
            pynutil.delete(ORDINAL_YEAR_WORD.upper() + NEMO_SPACE),
        )

        day_mappings = load_labels(get_abs_path("data/date/days.tsv"))
        month_mappings = load_labels(get_abs_path("data/date/months.tsv"))
        era_mappings = load_labels(get_abs_path("data/date/year_suffix.tsv"))

        one_or_two_digits = pynini.closure(NEMO_DIGIT, 1, 2)
        year_digit = pynini.closure(NEMO_DIGIT, 4, 4)
        year_digit_loose = pynini.closure(NEMO_DIGIT, 1, 4)
        separator = pynini.union("/", "-", ".")
        separator_no_slash = pynini.union("-", ".")

        day_convert = pynini.string_map([(k, v) for k, v in day_mappings])
        month_convert = pynini.string_map([(k, v) for k, v in month_mappings])
        year_convert = pynini.compose(year_digit, cardinal.graph)
        year_convert_loose = pynini.compose(year_digit_loose, cardinal.graph)

        era_to_full = {}
        for abbr, full_form in era_mappings:
            era_to_full[abbr.lower()] = full_form
            era_to_full[abbr.upper()] = full_form

        era_convert = pynini.string_map([(k, v) for k, v in era_to_full.items()])

        day_part = pynutil.insert("day: \"") + day_convert + pynutil.insert("\" ")
        month_part = pynutil.insert("month: \"") + month_convert + pynutil.insert("\" ")
        year_part = pynutil.insert("year: \"") + year_convert + pynutil.insert("\"")
        year_part_loose = pynutil.insert("year: \"") + year_convert_loose + pynutil.insert("\"")
        month_final = pynutil.insert("month: \"") + month_convert + pynutil.insert("\"")
        era_part = pynutil.insert("era: \"") + era_convert + pynutil.insert("\"")
        quarter_roman_to_digit = pynini.string_map(
            [
                ("I", "1"),
                ("II", "2"),
                ("III", "3"),
                ("IV", "4"),
                ("i", "1"),
                ("ii", "2"),
                ("iii", "3"),
                ("iv", "4"),
            ]
        )
        quarter_digit = pynini.union("1", "2", "3", "4")
        quarter_value = pynini.union(quarter_digit, quarter_roman_to_digit) @ cardinal.graph
        quarter_part = pynutil.insert("quarter: \"") + quarter_value + pynutil.insert("\" ")

        patterns = []

        # DD/MM/YYYY format (Vietnamese standard)
        # Require consistent separators within a date to avoid ambiguities like "4-5/2026"
        # which is more naturally a month range (4-5)/2026.
        date_sep = day_part + pynutil.delete(separator) + month_part + pynutil.delete(separator) + year_part
        for sep in [pynini.accep("/"), pynini.accep("-"), pynini.accep(".")]:
            patterns.append(
                pynutil.add_weight(
                    pynini.compose(one_or_two_digits + sep + one_or_two_digits + sep + year_digit, date_sep),
                    -2.0,
                )
            )

        # Allow 1-4 digit years for slash-separated D/M/Y (e.g., 1/3/20).
        # Keep this slightly lower priority than the strict 4-digit rule.
        date_sep_loose = (
            day_part
            + pynutil.delete(pynini.accep("/"))
            + month_part
            + pynutil.delete(pynini.accep("/"))
            + year_part_loose
        )
        patterns.append(
            pynutil.add_weight(
                pynini.compose(
                    one_or_two_digits + pynini.accep("/") + one_or_two_digits + pynini.accep("/") + year_digit_loose,
                    date_sep_loose,
                ),
                0.01,
            )
        )

        # Quarter/year with separators: quý III/2017, quý 3-2017, Quý III.2017
        for sep in [pynini.accep("/"), pynini.accep("-"), pynini.accep(".")]:
            quarter_year_sep = (
                quarter_part
                + pynutil.delete(pynini.closure(NEMO_SPACE, 0, 1))
                + pynutil.delete(sep)
                + pynutil.delete(pynini.closure(NEMO_SPACE, 0, 1))
                + year_part_loose
            )
            patterns.append(
                pynutil.add_weight(
                    pynini.compose(
                        quarter_prefix
                        + pynini.union(quarter_digit, quarter_roman_to_digit)
                        + pynini.closure(NEMO_SPACE, 0, 1)
                        + sep
                        + pynini.closure(NEMO_SPACE, 0, 1)
                        + year_digit_loose,
                        quarter_prefix_keep + quarter_year_sep,
                    ),
                    -0.5,
                )
            )
        for sep in [pynini.accep("/"), pynini.accep("-"), pynini.accep(".")]:
            patterns.append(
                pynutil.add_weight(
                    pynini.compose(
                        day_prefix + one_or_two_digits + sep + one_or_two_digits + sep + year_digit,
                        day_prefix_keep + date_sep,
                    ),
                    -2.0,
                )
            )

        patterns.append(
            pynutil.add_weight(
                pynini.compose(
                    day_prefix
                    + one_or_two_digits
                    + pynini.accep("/")
                    + one_or_two_digits
                    + pynini.accep("/")
                    + year_digit_loose,
                    day_prefix_keep + date_sep_loose,
                ),
                0.01,
            )
        )

        for sep in [pynini.accep("/"), pynini.accep("-"), pynini.accep(".")]:
            patterns.append(
                pynutil.add_weight(
                    context_prefix
                    + pynini.compose(
                        one_or_two_digits + sep + one_or_two_digits + sep + year_digit,
                        date_sep,
                    ),
                    -0.02,
                )
            )

        patterns.append(
            pynutil.add_weight(
                context_prefix
                + pynini.compose(
                    one_or_two_digits
                    + pynini.accep("/")
                    + one_or_two_digits
                    + pynini.accep("/")
                    + year_digit_loose,
                    date_sep_loose,
                ),
                0.01,
            )
        )

        # YYYY/MM/DD format (ISO standard) - output in Vietnamese order
        iso_year_part = pynutil.insert("year: \"") + year_convert + pynutil.insert("\" ")
        iso_month_part = pynutil.insert("month: \"") + month_convert + pynutil.insert("\" ")
        iso_day_part = pynutil.insert("day: \"") + day_convert + pynutil.insert("\"")

        iso_date_sep = (
            iso_year_part + pynutil.delete(separator) + iso_month_part + pynutil.delete(separator) + iso_day_part
        )
        for sep in [pynini.accep("/"), pynini.accep("-"), pynini.accep(".")]:
            patterns.append(
                pynutil.add_weight(
                    pynini.compose(year_digit + sep + one_or_two_digits + sep + one_or_two_digits, iso_date_sep),
                    -2.0,
                )
            )

        for sep in [pynini.accep("/"), pynini.accep("-"), pynini.accep(".")]:
            patterns.append(
                context_prefix
                + pynini.compose(
                    year_digit + sep + one_or_two_digits + sep + one_or_two_digits,
                    iso_date_sep,
                )
            )

        for sep in [separator, pynini.accep(NEMO_SPACE)]:
            patterns.append(
                pynini.compose(
                    month_prefix + one_or_two_digits + sep + year_digit_loose,
                    month_prefix_keep + month_part + pynutil.delete(sep) + year_part_loose,
                )
            )

        # Bare MM/YYYY without explicit "tháng" prefix.
        # This is common in Vietnamese text (e.g., "12/2026") but can be ambiguous with fractions.
        # Give it a slightly higher priority so it is preferred in typical running text.
        patterns.append(
            pynutil.add_weight(
                context_prefix
                + pynini.compose(
                    one_or_two_digits + separator + year_digit,
                    month_part + pynutil.delete(separator) + year_part,
                ),
                -0.01,
            )
        )

        day_month_sep = day_part + pynutil.delete(separator) + month_final
        two_digit_month_10_12 = pynini.union("10", "11", "12")

        # D/M with explicit "ngày" prefix: ngày 20/1, ngày 20/01
        # Without this, slash forms may fall back to fraction parsing (20/1 -> hai mươi phần một).
        patterns.append(
            pynutil.add_weight(
                pynini.compose(
                    day_prefix + one_or_two_digits + pynini.accep("/") + one_or_two_digits,
                    day_prefix_keep + day_part + pynutil.delete("/") + month_final,
                ),
                -0.02,
            )
        )

        patterns.append(
            pynutil.add_weight(
                context_prefix
                + pynini.compose(
                    one_or_two_digits + pynini.accep("/") + one_or_two_digits,
                    day_part + pynutil.delete("/") + month_final,
                ),
                -0.01,
            )
        )

        # DD-MM and DD.MM without explicit "ngày" prefix.
        # This is common in Vietnamese text and avoids ambiguity with fractions for the '/' separator.
        # Give it a slightly higher priority than splitting into separate cardinals (e.g., 15-5 -> 15 and -5).
        patterns.append(
            pynutil.add_weight(
                pynini.compose(
                    context_prefix + one_or_two_digits + separator_no_slash + one_or_two_digits,
                    context_prefix + day_month_sep,
                ),
                -0.01,
            )
        )

        patterns.append(
            pynini.compose(
                day_prefix
                + one_or_two_digits
                + pynini.accep(NEMO_SPACE + MONTH_WORD + NEMO_SPACE)
                + one_or_two_digits,
                day_prefix_keep + day_part + pynutil.delete(NEMO_SPACE + MONTH_WORD + NEMO_SPACE) + month_final,
            )
        )

        patterns.append(
            pynini.compose(
                day_prefix
                + one_or_two_digits
                + pynini.accep(NEMO_SPACE + MONTH_WORD + NEMO_SPACE)
                + one_or_two_digits
                + pynini.accep(NEMO_SPACE + YEAR_WORD + NEMO_SPACE)
                + year_digit_loose,
                day_prefix_keep
                + day_part
                + pynutil.delete(NEMO_SPACE + MONTH_WORD + NEMO_SPACE)
                + month_part
                + pynutil.delete(NEMO_SPACE + YEAR_WORD + NEMO_SPACE)
                + year_part_loose,
            )
        )

        patterns.append(pynini.compose(year_prefix + year_digit, year_prefix_keep + year_part))

        era_abbrs = list(era_to_full.keys())
        for era_abbr in era_abbrs:
            patterns.append(
                pynini.compose(
                    year_prefix + year_digit + pynini.accep(NEMO_SPACE) + pynini.accep(era_abbr),
                    year_prefix_keep + year_part + pynutil.delete(NEMO_SPACE) + era_part,
                )
            )

            patterns.append(
                pynini.compose(
                    ordinal_year_prefix + year_digit + pynini.accep(NEMO_SPACE) + pynini.accep(era_abbr),
                    ordinal_year_prefix_keep
                    + pynutil.insert("ordinal: \"")
                    + year_convert
                    + pynutil.insert("\" ")
                    + pynutil.delete(NEMO_SPACE)
                    + era_part,
                )
            )

        self.fst = self.add_tokens(pynini.union(*patterns))
