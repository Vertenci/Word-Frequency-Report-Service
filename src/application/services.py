import re
from typing import Dict, List, Tuple
from src.domain.entities import WordStats
from src.domain.interfaces import Lemmatizer


class LemmatizerService:
    def __init__(self, lemmatizer: Lemmatizer):
        self.lemmatizer = lemmatizer

    def process_line_batch(self, lines: List[Tuple[int, str]]) -> Dict[str, WordStats]:
        local_stats: Dict[str, WordStats] = {}

        for line_num, line in lines:
            words = self._split_words(line)

            for word in words:
                if not word:
                    continue

                lemma = self.lemmatizer.lemmatize(word.lower())

                if lemma not in local_stats:
                    local_stats[lemma] = WordStats(word=lemma)

                word_stat = local_stats[lemma]
                word_stat.total_count += 1

                while len(word_stat.line_counts) <= line_num:
                    word_stat.line_counts.append(0)
                word_stat.line_counts[line_num] += 1

        return local_stats

    def _split_words(self, line: str) -> List[str]:
        words = re.findall(r'[а-яА-ЯёЁa-zA-Z]+', line)
        return words
