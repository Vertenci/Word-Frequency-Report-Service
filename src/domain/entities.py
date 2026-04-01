from dataclasses import dataclass, field


@dataclass
class WordStats:
    word: str
    total_count: int = 0
    line_counts: list[int] = field(default_factory=list)

    def to_excel_row(self) -> tuple:
        counts_str = ','.join(str(c) for c in self.line_counts)
        return (self.word, self.total_count, counts_str)


@dataclass
class ProcessingResult:
    filename: str
    stats: dict[str, WordStats]
    total_lines: int