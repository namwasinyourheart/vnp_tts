from gliner2 import GLiNER2
import torch

device = "cuda:0" if torch.cuda.is_available() else "cpu"
print("Using device:", device)

# Load the model
extractor = GLiNER2.from_pretrained("fastino/gliner2-base-v1")

extractor = extractor.to(device)

# Extract entities with descriptions for higher precision
# text = "Patient received 400mg ibuprofen for severe headache at 2 PM."
text = "By March 4, 2026, the research team had completed the report, with 3/5 samples meeting the required standards"

text = "On April 3rd, the research team completed the report, with 3 out of 5 samples meeting the required standards"

import time 
start_time = time.time()
result = extractor.extract_entities(
    text,
    {
        # "PERSON": "Names of people, including real individuals or fictional characters",
        # "ORG": "Names of organizations such as companies, institutions, or agencies",
        # "LOCATION": "Geographical locations like countries, cities, regions, or landmarks",
        "DATE": "Dates in any format, including specific or relative dates (e.g., 'April 5', 'last year')",
        "TIME": "Specific times of the day (e.g., '2 PM', 'morning', 'evening')",
        "RATIO": "Ratio expressions (e.g., '3/5', 'two-thirds')",
        # "NUMBER": "Numeric values, quantities, or measurements (e.g., '10', '5kg', 'three')",
        # "FACILITY": "Names of buildings, infrastructures, or facilities (e.g., hospitals, airports, highways)",
        # "PRODUCT": "Names of products, objects, or branded items (e.g., iPhone, Toyota Camry, Coca-Cola)",
        # "WORK_OF_ART": "Titles of creative works such as books, movies, songs, or paintings",
        # "LANGUAGE": "Names of natural languages or programming languages (e.g., English, Python)",
        # "NORP": "Nationalities, religious groups, or political groups (e.g., Vietnamese, Muslim, Democrats)",
        # "ADDRESS": "Full or partial physical addresses (e.g., '123 Main St, Hanoi')",
        # "PHONE_NUMBER": "Telephone or mobile phone numbers"
        }
)

end_time = time.time()
print(result)
print(f"Time: {end_time - start_time}")
# Output: {'entities': {'medication': ['ibuprofen'], 'dosage': ['400mg'], 'symptom': ['severe headache'], 'time': ['2 PM']}}
