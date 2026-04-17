import string

import pynini
from pynini.lib import pynutil

from nemo_text_processing.text_normalization.vi.graph_utils import NEMO_DIGIT, GraphFst, convert_space
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


def _load_measure_units():
    """Load measure unit abbreviations from existing measure data files."""
    units = []
    # Load base units (m, g, l, s, v, w, hz, A, b, B, pa, ω, Ω, h, min, hr)
    base_path = get_abs_path("data/measure/base_units.tsv")
    try:
        base_units = load_labels(base_path)
        # Convert from list of lists to list of tuples
        units.extend([(k, v) for k, v in base_units])
    except Exception:
        pass
    # Load prefixes (k, M, G, T, P, E, h, da, d, c, m, µ, n, p, f)
    prefix_path = get_abs_path("data/measure/prefixes.tsv")
    try:
        prefixes = load_labels(prefix_path)
        # Create combined units from prefixes + base units (e.g., km, kg, cm, mm, MHz)
        base_units_dict = dict(base_units) if base_units else {}
        for p_key, p_val in prefixes:
            for b_key, b_val in base_units_dict.items():
                # Combine: km -> "ki lô mét", kg -> "ki lô gam", etc.
                combined_key = p_key + b_key
                combined_val = p_val + " " + b_val
                units.append((combined_key, combined_val))
                # Also add lowercase version
                units.append((combined_key.lower(), combined_val))
    except Exception:
        pass
    # Load additional measurements (ha, mi, ft, inch, yd, %, hp, rad, kwh, kbps, etc.)
    minimal_path = get_abs_path("data/measure/measurements_minimal.tsv")
    try:
        minimal_units = load_labels(minimal_path)
        # Filter out non-unit entries like "cái", "chiếc", "nghìn", etc. and convert to tuples
        filtered = [(k, v) for k, v in minimal_units if k not in {
            "cái", "chiếc", "nghìn", "trăm", "triệu", "tỷ", "độ"
        }]
        units.extend(filtered)
    except Exception:
        pass
    return units


class AlphanumericFst(GraphFst):
    """Classifies mixed letter-number tokens, e.g. 2A, K12, A2B, 2A3."""

    def __init__(self, cardinal: GraphFst, deterministic: bool = True):
        super().__init__(name="alphanumeric", kind="classify", deterministic=deterministic)

        letter_pairs = _load_letter_sounds(get_abs_path("data/alphanumeric_letter_sound_vn_iy.txt"))
        letter_unit = pynini.string_map(letter_pairs).optimize()
        letter_pairs_no_hour = [(k, v) for k, v in letter_pairs if k not in {"h", "H"}]
        letter_unit_no_hour = pynini.string_map(letter_pairs_no_hour).optimize()

        letter_seq = letter_unit + pynini.closure(pynutil.insert(" ") + letter_unit)
        letter_seq_no_hour = letter_unit_no_hour + pynini.closure(pynutil.insert(" ") + letter_unit)
        digit_seq = pynini.closure(NEMO_DIGIT, 1)
        number_seq = digit_seq @ cardinal.graph

        # Load measure units and create number+unit pattern (e.g., 45km -> "bốn mươi lăm ki lô mét")
        measure_units = _load_measure_units()
        if measure_units:
            unit_map = pynini.string_map(measure_units).optimize()
            # number + unit pattern with higher priority (lower weight)
            number_unit = number_seq + pynutil.insert(" ") + unit_map
            # Give it a slight negative weight to prioritize over letter-by-letter reading
            number_unit = pynutil.add_weight(number_unit, -0.1)
        else:
            number_unit = None

        # Highly certain unit-like prefixes should be prioritized over spelling letters one-by-one.
        km_prefix = pynini.union("Km", "KM", "km", "kM")
        km_number = pynini.cross(km_prefix, "ki lô mét") + pynutil.insert(" ") + number_seq

        l_d = letter_seq + pynutil.insert(" ") + number_seq
        d_l = number_seq + pynutil.insert(" ") + letter_seq_no_hour
        l_d_l = letter_seq + pynutil.insert(" ") + number_seq + pynutil.insert(" ") + letter_seq
        d_l_d = number_seq + pynutil.insert(" ") + letter_seq_no_hour + pynutil.insert(" ") + number_seq

        # Combine all patterns, with number+unit having priority
        if number_unit is not None:
            self.graph = (number_unit | km_number | l_d | d_l | l_d_l | d_l_d).optimize()
        else:
            self.graph = (km_number | l_d | d_l | l_d_l | d_l_d).optimize()
        self.final_graph = convert_space(self.graph).optimize()
        self.fst = (pynutil.insert('value: "') + self.final_graph + pynutil.insert('"')).optimize()
        self.fst = self.add_tokens(self.fst)
