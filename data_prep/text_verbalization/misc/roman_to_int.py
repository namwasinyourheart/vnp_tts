# class Solution:
#     def romanToInt(self, s: str) -> int:
#         result = 0
#         symbol_value = {
#             "I": 1,
#             "V": 5,
#             "X": 10,
#             "L": 50,
#             "C": 100,
#             "D": 500,
#             "M": 1000
#         }
#         for i in range(len(s)-1):
#             if symbol_value[s[i]] >= symbol_value[s[i+1]]:
#                 result += symbol_value[s[i]]
#             else:
#                 result -= symbol_value[s[i]]

#         return result + symbol_value[s[-1]]






# solution = Solution()
# print(solution.romanToInt(s = "III"))
# print(solution.romanToInt(s = "LVIII"))
# print(solution.romanToInt(s = "MCMXCIV"))


import re

ROMAN_MAP = {
    'I':1,'V':5,'X':10,
    'L':50,'C':100,
    'D':500,'M':1000
}

# Pattern to match potential Roman numerals (only containing valid Roman numeral characters)
roman_pattern = re.compile(r'\b[MDCLXVI]+\b', re.IGNORECASE)

# Roman -> Integer
def roman_to_int(s):
    total = 0
    prev = 0
    for c in reversed(s.upper()):
        val = ROMAN_MAP.get(c)
        if val is None:
            return None  # Invalid Roman numeral
        if val < prev:
            total -= val
        else:
            total += val
        prev = val
    return total

# Validate if a string is a valid Roman numeral
def is_valid_roman(s):
    s = s.upper()
    # Check if all characters are valid Roman numeral characters
    if not all(c in ROMAN_MAP for c in s):
        return False
    
    # Check if it follows valid Roman numeral patterns
    # Valid pattern: M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})
    valid_pattern = re.compile(
        r'^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$'
    )
    return bool(valid_pattern.match(s))

digits = [
    "không","một","hai","ba","bốn",
    "năm","sáu","bảy","tám","chín"
]

def number_to_vietnamese(n):

    if n < 10:
        return digits[n]

    if n < 20:
        if n == 10:
            return "mười"
        return "mười " + digits[n % 10]

    if n < 100:
        tens = n // 10
        ones = n % 10

        if ones == 0:
            return digits[tens] + " mươi"

        if ones == 1:
            return digits[tens] + " mươi mốt"

        if ones == 5:
            return digits[tens] + " mươi lăm"

        return digits[tens] + " mươi " + digits[ones]

    return str(n)  # fallback


def normalize_roman(text):
    """
    Normalize Roman numerals in text to Vietnamese spoken form.
    Only converts valid Roman numerals, leaves other text unchanged.
    """
    def replace(match):
        roman = match.group(0)
        
        # Validate if it's a proper Roman numeral
        if not is_valid_roman(roman):
            return roman  # Keep original if not valid
        
        value = roman_to_int(roman)
        if value is None:
            return roman  # Keep original if conversion failed
        
        spoken = number_to_vietnamese(value)
        return spoken

    return roman_pattern.sub(replace, text)

print(roman_to_int("III"))
print(roman_to_int("LVIII"))
print(roman_to_int("MCMXCIV"))

# Test with sentences
test_sentences = [
    "quý III, năm LVIII, MCMXCIV năm 2025, thế kỷ XIX.",
    "Chương IV và chương V rất quan trọng.",
    "Thế kỷ XX là thế kỷ của khoa học.",
    "Louis XIV là vua của Pháp.",
    "IV III LVIII MCMXCIV",
    'Ông Nguyễn Duy Ngọc sinh năm 1964, quê ở Hưng Yên. Ông có trình độ chuyên môn Thạc sĩ Luật, là Ủy viên Trung ương Đảng khóa XIII, XIV; Ủy viên Bộ Chính trị khóa XIII, XIV.'
]

print("\n--- Sentence Normalization ---")
for sentence in test_sentences:
    normalized = normalize_roman(sentence)
    print(f"Original:    {sentence}")
    print(f"Normalized:  {normalized}")
    print()