# tanaos/tanaos-NER-v1

from dataclasses import dataclass
from typing import List
from artifex import Artifex
import time


@dataclass
class NEREntity:
    entity_group: str
    word: str
    score: float
    start: int
    end: int


def merge_entities(entities: List[NEREntity], text: str) -> List[NEREntity]:
    """Merge adjacent entities of the same type into continuous spans."""
    if not entities:
        return []

    # Sort by start position
    sorted_entities = sorted(entities, key=lambda e: e.start)

    merged = []
    current = sorted_entities[0]

    for next_entity in sorted_entities[1:]:
        # Check if same type and adjacent (with possible whitespace gap)
        if next_entity.entity_group == current.entity_group and next_entity.start <= current.end + 1:
            # Merge: extend end, take text from original string, average score
            current = NEREntity(
                entity_group=current.entity_group,
                word=text[current.start:next_entity.end],
                score=(current.score + next_entity.score) / 2,
                start=current.start,
                end=next_entity.end
            )
        else:
            merged.append(current)
            current = next_entity

    merged.append(current)
    return merged


ner = Artifex().named_entity_recognition()

text = "Ngày 08/4, Tổng công ty Bưu điện Việt Nam triển khai tổ chức Hội nghị triển khai các quyết định về công tác cán bộ "
text = " Quy tắc tỉ lệ 1/3 cũng rất hữu ích "
text = "Hôm nay là ngày 12/04, đội nghiên cứu đã hoàn thành báo cáo với tỉ lệ 3/5 mẫu đạt chuẩn."

text = "It is anticipated that by April 30th, the group will increase its success rate to approximately two-thirds, assuming everything goes according to plan."

text = "By March 4, 2026, the research team had completed the report, with 3 out of 5 samples meeting the required standards."

text = "The office is located at No. 5 Phạm Hùng, Nam Từ Liêm District, Hanoi."

text = "Mr. Nguyen Manh Hai, 30 years old, residing in Thien Huong ward, Hai Phong city, has been married for 10 years. After getting married, Mr. Hai inherited a small house built in 2010 from his parents, located on a 150m2 plot of land."

text = "On April 3rd, the research team completed the report, with 3 out of 5 samples meeting the required standards"

start_time = time.time()

raw_entities = ner(text)
# Handle both dict and NEREntity objects
def to_ner_entity(e):
    if isinstance(e, dict):
        return NEREntity(
            entity_group=e['entity_group'],
            word=e['word'],
            score=e['score'],
            start=e['start'],
            end=e['end']
        )
    else:
        # Already an object with attributes
        return NEREntity(
            entity_group=getattr(e, 'entity_group', e[0] if hasattr(e, '__getitem__') else None),
            word=getattr(e, 'word', e[2] if hasattr(e, '__getitem__') else None),
            score=getattr(e, 'score', e[1] if hasattr(e, '__getitem__') else None),
            start=getattr(e, 'start', e[3] if hasattr(e, '__getitem__') else None),
            end=getattr(e, 'end', e[4] if hasattr(e, '__getitem__') else None)
        )

# raw_entities might be a list of lists or list of objects
if raw_entities and len(raw_entities) > 0:
    first_item = raw_entities[0]
    if isinstance(first_item, list):
        entities = [to_ner_entity(e) for e in first_item]
    else:
        entities = [to_ner_entity(e) for e in raw_entities]
else:
    entities = []

# Merge adjacent entities
merged_entities = merge_entities(entities, text)
print(merged_entities)
print(f"Time: {time.time() - start_time}")



# >>> [[{'entity_group': 'PERSON', 'score': 0.92174554, 'word': 'John', 'start': 0, 'end': 4}, {'entity_group': 'LOCATION', 'score': 0.9853817, 'word': ' Barcelona', 'start': 15, 'end': 24}, {'entity_group': 'TIME', 'score': 0.98645407, 'word': ' 15:45.', 'start': 28, 'end': 34}]]
