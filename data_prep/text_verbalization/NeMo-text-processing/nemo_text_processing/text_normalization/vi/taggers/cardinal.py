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

from nemo_text_processing.text_normalization.vi.graph_utils import NEMO_DIGIT, GraphFst, insert_space
from nemo_text_processing.text_normalization.vi.utils import get_abs_path, load_labels


class CardinalFst(GraphFst):
    def __init__(self, deterministic: bool = True):
        super().__init__(name="cardinal", kind="classify", deterministic=deterministic)

        resources = {
            'zero': pynini.string_file(get_abs_path("data/numbers/zero.tsv")),
            'digit': pynini.string_file(get_abs_path("data/numbers/digit.tsv")),
            'teen': pynini.string_file(get_abs_path("data/numbers/teen.tsv")),
            'ties': pynini.string_file(get_abs_path("data/numbers/ties.tsv")),
        }
        self.zero, self.digit, self.teen, self.ties = resources.values()

        magnitudes_labels = load_labels(get_abs_path("data/numbers/magnitudes.tsv"))
        self.magnitudes = {parts[0]: parts[1] for parts in magnitudes_labels if len(parts) == 2}

        digit_special_labels = load_labels(get_abs_path("data/numbers/digit_special.tsv"))
        special = {parts[0]: {'std': parts[1], 'alt': parts[2]} for parts in digit_special_labels if len(parts) >= 3}

        self.special_digits = pynini.union(
            *[pynini.cross(k, v["alt"]) for k, v in special.items() if k in ["1", "4", "5"]]
        )
        digit_except_4 = pynini.union("1", "2", "3", "5", "6", "7", "8", "9") @ self.digit
        self.linh_digits = pynini.union(
            pynini.cross("4", special["4"]["alt"]),
            *[pynini.cross(k, special[k]["std"]) for k in ["1", "5"]],
            digit_except_4,
        )

        self.single_digits_graph = self.digit | self.zero

        # Multi-digit strings with leading zeros should be read digit-by-digit.
        # Examples: "04" -> "không bốn", "000823" -> "không không không tám hai ba".
        digit_by_digit = self.single_digits_graph + pynini.closure(insert_space + self.single_digits_graph)
        leading_zero_multi = pynini.accep("0") + pynini.closure(NEMO_DIGIT, 1)
        leading_zero_by_digit = pynutil.add_weight(leading_zero_multi @ digit_by_digit, -0.1)

        # Helper: chunk digits pattern for 8+ digit numbers (no separator).
        # Chunks are 3 or 4 digits, separated by comma pause.
        def _chunk_digits(n: int):
            """Return list of chunk sizes for n digits."""
            if n % 4 == 0:
                return [4] * (n // 4)
            if n % 3 == 0:
                return [3] * (n // 3)
            if n % 3 == 1:
                return [3] * (n // 3 - 1) + [3, 4]
            if n % 3 == 2:
                return [3] * (n // 3 - 2) + [4, 4]
            return [n]

        # Build pattern for 8-20 digit numbers with chunking
        multi_digit_by_digit_chunks = None
        for length in range(8, 21):  # 8 to 20 digits covers long account numbers, codes
            chunks = _chunk_digits(length)
            # Build pattern: digit groups with comma separator
            pos = 0
            chunk_patterns = []
            for i, size in enumerate(chunks):
                chunk_pat = pynini.closure(NEMO_DIGIT, size, size)
                chunk_out = chunk_pat @ digit_by_digit
                if i > 0:
                    chunk_out = pynutil.insert(", ") + chunk_out
                chunk_patterns.append((pos, size, chunk_out))
                pos += size
            # Compose full pattern
            full_pat = None
            for _, _, out in chunk_patterns:
                if full_pat is None:
                    full_pat = out
                else:
                    full_pat = full_pat + out
            # Create input acceptor for this exact length
            input_acceptor = pynini.closure(NEMO_DIGIT, length, length)
            full_pat = input_acceptor @ full_pat
            if multi_digit_by_digit_chunks is None:
                multi_digit_by_digit_chunks = full_pat
            else:
                multi_digit_by_digit_chunks = multi_digit_by_digit_chunks | full_pat
        multi_digit_by_digit_chunks = pynutil.add_weight(multi_digit_by_digit_chunks, -1.0)

        # Pattern for >20 digits: read digit-by-digit without comma pauses
        # Just spaces between digits
        multi_digit_by_digit_no_chunks = None
        for length in range(21, 31):  # 21 to 30 digits
            input_acceptor = pynini.closure(NEMO_DIGIT, length, length)
            full_pat = input_acceptor @ digit_by_digit
            if multi_digit_by_digit_no_chunks is None:
                multi_digit_by_digit_no_chunks = full_pat
            else:
                multi_digit_by_digit_no_chunks = multi_digit_by_digit_no_chunks | full_pat
        multi_digit_by_digit_no_chunks = pynutil.add_weight(multi_digit_by_digit_no_chunks, -1.0)

        self.two_digit = pynini.union(
            self.teen,
            self.ties + pynutil.delete("0"),
            self.ties
            + insert_space
            + pynini.union(self.special_digits, pynini.union("2", "3", "6", "7", "8", "9") @ self.digit),
        )

        hundred_word = self.magnitudes["hundred"]
        linh_word = self.magnitudes["linh"]

        # X00: một trăm, hai trăm, etc.
        hundreds_exact = self.digit + insert_space + pynutil.insert(hundred_word) + pynutil.delete("00")

        # X0Y: một trăm linh một, hai trăm linh năm, etc.
        hundreds_with_linh = (
            self.digit
            + insert_space
            + pynutil.insert(hundred_word)
            + pynutil.delete("0")
            + insert_space
            + pynutil.insert(linh_word)
            + insert_space
            + self.linh_digits
        )

        # XYZ: một trăm hai mười ba, etc.
        hundreds_with_tens = self.digit + insert_space + pynutil.insert(hundred_word) + insert_space + self.two_digit

        # 0YZ: Handle numbers starting with 0 (e.g., 087 -> tám mươi bảy)
        leading_zero_tens = pynutil.delete("0") + self.two_digit

        # 00Z: Handle numbers starting with 00 (e.g., 008 -> tám)
        leading_double_zero = pynutil.delete("00") + self.digit

        self.hundreds_pattern = pynini.union(
            hundreds_exact,
            hundreds_with_linh,
            hundreds_with_tens,
            leading_zero_tens,
            leading_double_zero,
        )

        grouped_leading_zero_tens = (
            pynutil.delete("0")
            + pynutil.insert("không")
            + insert_space
            + pynutil.insert(hundred_word)
            + insert_space
            + self.two_digit
        )

        grouped_leading_double_zero = (
            pynutil.delete("00")
            + pynutil.insert("không")
            + insert_space
            + pynutil.insert(hundred_word)
            + insert_space
            + pynutil.insert(linh_word)
            + insert_space
            + self.linh_digits
        )

        self.hundreds_pattern_grouped = pynini.union(
            hundreds_exact,
            hundreds_with_linh,
            hundreds_with_tens,
            grouped_leading_zero_tens,
            grouped_leading_double_zero,
        )

        self.hundreds = pynini.closure(NEMO_DIGIT, 3, 3) @ self.hundreds_pattern

        self.magnitude_patterns = self._build_all_magnitude_patterns()
        custom_patterns = self._build_all_patterns()

        all_patterns = [
            leading_zero_by_digit,
            multi_digit_by_digit_chunks,
            multi_digit_by_digit_no_chunks,
            *custom_patterns,
            *self.magnitude_patterns.values(),
            self.hundreds,
            self.two_digit,
            self.digit,
            self.zero,
        ]
        self.graph = pynini.union(*all_patterns).optimize()

        negative = pynini.closure(pynutil.insert("negative: ") + pynini.cross("-", "\"true\" "), 0, 1)
        final_graph = negative + pynutil.insert("integer: \"") + self.graph + pynutil.insert("\"")
        self.fst = self.add_tokens(final_graph).optimize()

    def _build_magnitude_pattern(self, name, min_digits, max_digits, zero_count, prev_pattern=None):
        magnitude_word = self.magnitudes[name]
        linh_word = self.magnitudes["linh"]
        patterns = []

        for digits in range(min_digits, max_digits + 1):
            leading_digits = digits - zero_count
            if leading_digits == 1:
                leading_fst = self.digit
            elif leading_digits == 2:
                leading_fst = self.two_digit
            else:
                leading_fst = self.hundreds_pattern_grouped

            prefix = leading_fst + insert_space + pynutil.insert(magnitude_word)
            digit_patterns = [prefix + pynutil.delete("0" * zero_count)]

            if prev_pattern and name not in ["quadrillion", "quintillion"]:
                digit_patterns.append(prefix + insert_space + prev_pattern)

            for trailing_zeros in range(zero_count):
                remaining_digits = zero_count - trailing_zeros
                trailing_prefix = prefix + pynutil.delete("0" * trailing_zeros)

                if remaining_digits == 1:
                    if trailing_zeros % 3 == 2:
                        linh_pattern = (
                            trailing_prefix
                            + insert_space
                            + pynutil.insert("không")
                            + insert_space
                            + pynutil.insert(self.magnitudes["hundred"])
                            + insert_space
                            + pynutil.insert(linh_word)
                            + insert_space
                            + self.linh_digits
                        )
                        digit_patterns.append(pynutil.add_weight(linh_pattern, -0.1))
                    else:
                        linh_pattern = (
                            trailing_prefix + insert_space + pynutil.insert(linh_word) + insert_space + self.linh_digits
                        )
                        digit_patterns.append(pynutil.add_weight(linh_pattern, -0.1))
                elif remaining_digits == 2:
                    if trailing_zeros % 3 == 1:
                        digit_patterns.append(
                            trailing_prefix
                            + insert_space
                            + pynutil.insert("không")
                            + insert_space
                            + pynutil.insert(self.magnitudes["hundred"])
                            + insert_space
                            + self.two_digit
                        )
                    else:
                        digit_patterns.append(trailing_prefix + insert_space + self.two_digit)
                elif remaining_digits == 3:
                    digit_patterns.append(trailing_prefix + insert_space + self.hundreds_pattern)

            patterns.append(pynini.closure(NEMO_DIGIT, digits, digits) @ pynini.union(*digit_patterns))

        return pynini.union(*patterns)

    def _build_all_magnitude_patterns(self):
        magnitude_config = [
            ("thousand", 4, 6, 3),
            ("million", 7, 9, 6),
            ("billion", 10, 12, 9),
            ("trillion", 13, 15, 12),
            ("quadrillion", 16, 18, 15),
            ("quintillion", 19, 21, 18),
        ]
        patterns = {}
        prev_pattern = None
        for name, min_digits, max_digits, zero_count in magnitude_config:
            if name in self.magnitudes:
                patterns[name] = self._build_magnitude_pattern(name, min_digits, max_digits, zero_count, prev_pattern)
                prev_pattern = patterns[name]
            else:
                break
        return patterns

    def _get_zero_or_magnitude_pattern(self, digits, magnitude_key):
        """Create pattern that handles all-zeros or normal magnitude processing"""
        all_zeros = "0" * digits
        return pynini.union(pynini.cross(all_zeros, ""), NEMO_DIGIT**digits @ self.magnitude_patterns[magnitude_key])

    def _build_all_patterns(self):
        patterns = []
        delete_dot = pynutil.delete(".")
        delete_comma = pynutil.delete(",")

        # Large number split patterns (>12 digits): front + "tỷ" + back(9 digits)
        if "billion" in self.magnitudes:
            billion_word = self.magnitudes["billion"]
            back_digits = 9

            for total_digits in range(13, 22):
                front_digits = total_digits - back_digits
                front_pattern = self._get_pattern_for_digits(front_digits)
                if front_pattern:
                    back_pattern = self._get_zero_or_magnitude_pattern(back_digits, "million")
                    split_pattern = (
                        front_pattern + insert_space + pynutil.insert(billion_word) + insert_space + back_pattern
                    )
                    patterns.append(NEMO_DIGIT**total_digits @ pynutil.add_weight(split_pattern, -0.5))

        # Dot patterns
        dot_configs = [(6, None), (5, None), (4, None), (3, "billion"), (2, "million"), (1, "thousand")]
        for dots, magnitude in dot_configs:
            pattern = (NEMO_DIGIT - "0") + pynini.closure(NEMO_DIGIT, 0, 2)
            for _ in range(dots):
                pattern += delete_dot + NEMO_DIGIT**3

            if magnitude and magnitude in self.magnitude_patterns:
                patterns.append(pynini.compose(pynutil.add_weight(pattern, -0.3), self.magnitude_patterns[magnitude]))
            elif not magnitude:
                if dots == 4:
                    digit_range = [13, 14, 15]
                elif dots == 5:
                    digit_range = [16, 17, 18]
                elif dots == 6:
                    digit_range = [19, 20, 21]
                else:
                    digit_range = []

                for digit_count in digit_range:
                    if 13 <= digit_count <= 21:
                        front_digits = digit_count - back_digits
                        front_pattern = self._get_pattern_for_digits(front_digits)
                        if front_pattern:
                            back_pattern = self._get_zero_or_magnitude_pattern(back_digits, "million")
                            split = (
                                (NEMO_DIGIT**front_digits @ front_pattern)
                                + insert_space
                                + pynutil.insert(self.magnitudes["billion"])
                                + insert_space
                                + back_pattern
                            )
                            patterns.append(
                                pynini.compose(pattern, NEMO_DIGIT**digit_count @ pynutil.add_weight(split, -1.0))
                            )

        # Comma-grouped integer patterns (e.g., 1,000,000).
        # Treat commas as thousand separators, not decimal separators.
        comma_configs = [(6, None), (5, None), (4, None), (3, "billion"), (2, "million"), (1, "thousand")]
        for commas, magnitude in comma_configs:
            pattern = (NEMO_DIGIT - "0") + pynini.closure(NEMO_DIGIT, 0, 2)
            for _ in range(commas):
                pattern += delete_comma + NEMO_DIGIT**3

            if magnitude and magnitude in self.magnitude_patterns:
                patterns.append(pynini.compose(pynutil.add_weight(pattern, -0.3), self.magnitude_patterns[magnitude]))
            elif not magnitude:
                if commas == 4:
                    digit_range = [13, 14, 15]
                elif commas == 5:
                    digit_range = [16, 17, 18]
                elif commas == 6:
                    digit_range = [19, 20, 21]
                else:
                    digit_range = []

                for digit_count in digit_range:
                    if 13 <= digit_count <= 21:
                        front_digits = digit_count - back_digits
                        front_pattern = self._get_pattern_for_digits(front_digits)
                        if front_pattern:
                            back_pattern = self._get_zero_or_magnitude_pattern(back_digits, "million")
                            split = (
                                (NEMO_DIGIT**front_digits @ front_pattern)
                                + insert_space
                                + pynutil.insert(self.magnitudes["billion"])
                                + insert_space
                                + back_pattern
                            )
                            patterns.append(
                                pynini.compose(pattern, NEMO_DIGIT**digit_count @ pynutil.add_weight(split, -1.0))
                            )

        return patterns

    def _get_pattern_for_digits(self, digit_count):
        if digit_count <= 0:
            return None
        elif digit_count == 1:
            return self.digit
        elif digit_count == 2:
            return self.two_digit
        elif digit_count == 3:
            return self.hundreds_pattern
        elif digit_count <= 6:
            return self.magnitude_patterns.get("thousand")
        elif digit_count <= 9:
            return self.magnitude_patterns.get("million")
        elif digit_count <= 12:
            return self.magnitude_patterns.get("billion")
        else:
            return None
