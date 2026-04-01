import re
from src.domain.entities import WordStats
from src.domain.interfaces import Lemmatizer


class LemmatizerService:
    def __init__(self, lemmatizer: Lemmatizer):
        self.lemmatizer = lemmatizer

    def process_line(self, line: str, line_num: int, stats: dict[str, WordStats]) -> None:
        words = self._split_words(line)

        for word in words:
            if not word:
                continue

            lemma = self.lemmatizer.lemmatize(word)

            if lemma not in stats:
                stats[lemma] = WordStats(word=lemma, line_counts=[0] * (line_num + 1))

            word_stat = stats[lemma]

            word_stat.total_count += 1

            while len(word_stat.line_counts) <= line_num:
                word_stat.line_counts.append(0)

            word_stat.line_counts[line_num] += 1

    def _split_words(self, line: str) -> list[str]:
        words = re.findall(r'[а-яА-ЯёЁa-zA-Z]+', line)
        return words
