from src.domain.interfaces import Lemmatizer
from mawo_pymorphy3 import get_global_analyzer


class Pymorphy3Lemmatizer(Lemmatizer):
    def __init__(self):
        self._analyzer = get_global_analyzer()

    def lemmatize(self, word: str) -> str:
        if not word or len(word) < 2:
            return word.lower()

        try:
            parsed = self._analyzer.parse(word)
            if parsed:
                return parsed[0].normal_form.lower()
        except Exception:
            pass

        return word.lower()
