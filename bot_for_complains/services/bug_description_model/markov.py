from collections import Counter
from collections import defaultdict

from .normalize import normalize


class MarkovModel:

    def __init__(
        self,
        second_order_threshold: float,
        first_order_threshold: float,
        use_first_order: bool = True,
        bypass: bool = False,
    ):
        self.second = defaultdict(Counter)
        self.first = defaultdict(Counter)

        self.second_threshold = second_order_threshold
        self.first_threshold = first_order_threshold

        self.use_first_order = use_first_order
        self.bypass = bypass

    def fit(self, texts: list[str]):

        self.second.clear()
        self.first.clear()

        for text in texts:

            words = normalize(text).split()

            if len(words) < 2:
                continue

            for i in range(len(words)-1):
                self.first[words[i]][words[i+1]] += 1

            for i in range(len(words)-2):
                self.second[
                    (words[i], words[i+1])
                ][words[i+2]] += 1

    def score_second(self, text: str):

        words = normalize(text).split()

        if len(words) < 3:
            return 0

        ok = 0

        total = 0

        for i in range(len(words)-2):

            state = (
                words[i],
                words[i+1],
            )

            total += 1

            if words[i+2] in self.second[state]:
                ok += 1

        return ok / total if total else 0

    def score_first(self, text: str):

        words = normalize(text).split()

        if len(words) < 2:
            return 0

        ok = 0

        total = 0

        for i in range(len(words)-1):

            total += 1

            if words[i+1] in self.first[words[i]]:
                ok += 1

        return ok / total if total else 0

    def validate(self, text: str):

        if self.bypass:
            return True

        second = self.score_second(text)

        if second >= self.second_threshold:
            return True

        if not self.use_first_order:
            return False

        first = self.score_first(text)

        return first >= self.first_threshold
