from collections import Counter
from collections import defaultdict

from .normalize import normalize


class MarkovModel:
    """
    Марковская модель для проверки качества описания бага.

    Используются две цепи Маркова:

        • первого порядка:
            вероятность появления следующего слова
            по одному предыдущему.

        • второго порядка:
            вероятность появления следующего слова
            по двум предыдущим.

    Модель обучается только на корректных описаниях
    и проверяет, насколько новое описание похоже
    на обучающий корпус.
    """
    def __init__(
        self,
        second_order_threshold: float,
        first_order_threshold: float,
        use_first_order: bool = True,
        bypass: bool = False,
    ):
        """
        Parameters
        ----------
        second_order_threshold
            Минимальный порог для модели второго порядка.

        first_order_threshold
            Минимальный порог для модели первого порядка.

        use_first_order
            Использовать ли модель первого порядка
            как запасной вариант.

        bypass
            Полностью отключить проверку.
        """
        # (слово1, слово2) -> Counter(слово3)
        self.second = defaultdict(Counter)
        # слово1 -> Counter(слово2)
        self.first = defaultdict(Counter)

        self.second_threshold = second_order_threshold
        self.first_threshold = first_order_threshold

        self.use_first_order = use_first_order
        self.bypass = bypass

    def fit(self, texts: list[str]):
        """
        Обучение модели.

        На основе корпуса строятся частоты переходов:

            слово -> следующее слово

        и

            два слова -> следующее слово.
        """
        self.second.clear()
        self.first.clear()

        for text in texts:

            words = normalize(text).split()

            if len(words) < 2:
                continue
            # Строим модель первого порядка.
            for i in range(len(words)-1):
                self.first[words[i]][words[i+1]] += 1
            # Строим модель второго порядка.
            for i in range(len(words)-2):
                self.second[
                    (words[i], words[i+1])
                ][words[i+2]] += 1

    def score_second(self, text: str):
        """
        Оценка текста моделью второго порядка.

        Возвращает долю триграмм,
        найденных в обучающем корпусе.

        Значение находится в диапазоне:

            0.0 .. 1.0
        """
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
        """
        Оценка текста моделью первого порядка.

        Возвращает долю биграмм,
        найденных в обучающем корпусе.
        """
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
        """
        Проверка описания.

        Алгоритм:

        1. Если включён bypass → всегда True.

        2. Проверяем модель второго порядка.

        3. Если её оценка выше порога,
           описание считается корректным.

        4. Иначе при необходимости
           проверяем модель первого порядка.
        """
        if self.bypass:
            return True

        second = self.score_second(text)

        if second >= self.second_threshold:
            return True

        if not self.use_first_order:
            return False

        first = self.score_first(text)

        return first >= self.first_threshold
