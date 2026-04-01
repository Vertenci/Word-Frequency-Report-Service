from dataclasses import dataclass, field
from typing import List


@dataclass
class WordStats:
    word: str
    total_count: int = 0
    line_counts: List[int] = field(default_factory=list)

    def to_excel_row(self) -> tuple:
        counts_str = ','.join(str(c) for c in self.line_counts)
        return (self.word, self.total_count, counts_str)
