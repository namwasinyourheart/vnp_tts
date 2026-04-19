# import sys
# sys.path.append("/home/nampv1/projects/tts/vnp_tts/data_prep/text_verbalization")

import re
from typing import Optional, Callable, List, Dict, Any
from functools import partial

# Import all verbalization modules
from currency import verbalize_currency_sentence
from datetime import verbalize_datetime_sentence
from math import verbalize_math_sentence
from measure import verbalize_measure_sentence
from number import read_vietnamese_number

class TextVerbalizer:
    def __init__(self):
        # Define the order of verbalization processors
        self.processors: List[Callable[[str], str]] = [
            self._verbalize_numbers,
            self._verbalize_math_operations,
            self._verbalize_units,
            partial(verbalize_currency_sentence),
            partial(verbalize_datetime_sentence),
            partial(verbalize_math_sentence),
            partial(verbalize_measure_sentence),
        ]
    
    def _verbalize_numbers(self, text: str) -> str:
        """Convert standalone numbers to their Vietnamese verbal form."""
        def replace_number(match: re.Match) -> str:
            number_str = match.group(0)
            try:
                # Handle decimal numbers
                if '.' in number_str:
                    # Special case for temperature
                    if '°' in text[text.find(number_str) + len(number_str):]:
                        parts = number_str.split('.')
                        return ' phẩy '.join(read_vietnamese_number(part) for part in parts)
                    # Handle money format 1.000.000
                    if number_str.count('.') > 1:
                        return read_vietnamese_number(number_str.replace('.', ''))
                    # Regular decimal
                    parts = number_str.split('.')
                    return ' phẩy '.join(read_vietnamese_number(part) for part in parts)
                # Handle fractions
                if '/' in text[text.find(number_str) + len(number_str):]:
                    next_char = text[text.find(number_str) + len(number_str)]
                    if next_char == '/':
                        return read_vietnamese_number(number_str) + ' phần'
                return read_vietnamese_number(number_str)
            except (ValueError, IndexError):
                return number_str
        
        # Match standalone numbers (integers or decimals)
        pattern = r'(?<![\w/])(\d+[.,]?\d*)(?![\w/])'
        return re.sub(pattern, replace_number, text)
    
    def _verbalize_math_operations(self, text: str) -> str:
        """Convert mathematical operations to spoken form."""
        replacements = {
            '+': ' cộng ',
            '-': ' trừ ',
            '*': ' nhân ',
            '/': ' phần ',
            '=': ' bằng ',
            '  ': ' '  # Clean up double spaces
        }
        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
        return result.strip()
    
    def _verbalize_units(self, text: str) -> str:
        """Convert units to spoken form."""
        units = {
            '°C': ' độ C',
            '°F': ' độ F',
            'km': ' ki-lô-mét',
            'm': ' mét',
            'cm': ' xăng-ti-mét',
            'mm': ' mi-li-mét',
            'kg': ' ki-lô-gam',
            'g': ' gam',
            'l': ' lít',
            'ml': ' mi-li-lít',
            'đ': ' đồng',
            'vnd': ' đồng',
            'VND': ' đồng',
        }
        result = text
        for unit, spoken in units.items():
            result = result.replace(unit, spoken)
        return result
    
    def verbalize(self, text: str) -> str:
        """Convert written text to spoken text by applying all verbalization rules.
        
        Args:
            text: The input text to be verbalized
            
        Returns:
            The verbalized text with numbers, dates, times, currency, etc. converted to spoken form
        """
        if not text or not text.strip():
            return text
            
        # Apply each verbalization processor in sequence
        result = text
        for processor in self.processors:
            result = processor(result)
            
        return result

# Create a default instance for convenience
default_verbalizer = TextVerbalizer()

def verbalize(text: str) -> str:
    """Convenience function to verbalize text using the default verbalizer.
    
    Args:
        text: The input text to be verbalized
        
    Returns:
        The verbalized text
    """
    return default_verbalizer.verbalize(text)

# Example usage
if __name__ == "__main__":
    test_cases = [
        "Giá là 1.000.000đ, hạn đến 31/12/2023",
        "Nhiệt độ là 36.5°C",
        "Kết quả là 1/2 + 3/4 = 5/4",
        "Tôi có 2 cái bút và 3 quyển sách"
    ]
    
    print("=== Text Verbalization Examples ===")
    for test in test_cases:
        print(f"\nOriginal: {test}")
        print(f"Verbalized: {verbalize(test)}")