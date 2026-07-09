from collections import Counter
from collections import defaultdict
import logging

from .normalize import normalize
# проверка на похожисть на обучающий материал
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

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

        # используется ослабление строгости цепи Маркова с помощью проверки на похожость
        self.train_texts = []

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1,2),
        )

        self.train_vectors = None
        #----------------------------------------

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
        #---------------------------------------------
        self.train_texts = [
            normalize(text)
            for text in texts
        ]

        self.train_vectors = self.vectorizer.fit_transform(
            self.train_texts
        )
        #-------------------------------------------

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


        logger.info(
            "Марковская модель обучена: "
            "first_states=%d second_states=%d train_texts=%d",
            len(self.first),
            len(self.second),
            len(self.train_texts),
        )

    def similarity_score(self, text: str):
        """
        проверка на похожесть
        """
        if not self.train_texts:
            return 0


        normalized = normalize(text)


        vector = self.vectorizer.transform(
            [normalized]
        )


        scores = cosine_similarity(
            vector,
            self.train_vectors
        )[0]


        max_score = scores.max()


        index = scores.argmax()


        logger.debug(
            "Похожесть текста: "
            "score=%.3f similar='%s'",
            max_score,
            self.train_texts[index],
        )


        return max_score

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

        missed = []

        for i in range(len(words)-2):

            state = (
                words[i],
                words[i+1],
            )

            next_word = words[i+2]

            total += 1

            if next_word in self.second[state]:
                ok += 1
            else:
                missed.append(
                    f"{state} -> {next_word}"
                )
        score = ok / total if total else 0

        logger.debug(
            "Проверка второго порядка: "
            "score=%.3f ok=%d total=%d missed=%s",
            score,
            ok,
            total,
            missed[:10],
        )

        return score

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

        missed = []

        for i in range(len(words)-1):

            current = words[i]
            next_word = words[i+1]

            total += 1

            if next_word in self.first[current]:
                ok += 1
            else:
                missed.append(
                    f"{current} -> {next_word}"
                )

        score = ok / total if total else 0

        logger.debug(
            "Проверка первого порядка: "
            "score=%.3f ok=%d total=%d missed=%s",
            score,
            ok,
            total,
            missed[:10],
        )

        return score

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
            logger.warning(
                "Проверка отключена bypass=True. "
                "Описание принято: %s",
                text,
            )
            return True

        normalized = normalize(text)

        second = self.score_second(text)
        # оценка похожисти
        similarity = self.similarity_score(text)
        logger.debug(
            "Оценка описания: "
            "markov=%.3f similarity=%.3f text='%s'",
            second,
            similarity,
            normalized,
        )
        logger.debug(
            "Проверка описания: "
            "second=%.3f threshold=%.3f text='%s'",
            second,
            self.second_threshold,
            normalized,
        )
        # расчет финального счета
        final_score = (
            second * 0.4 +
            similarity * 0.6
        )
        # если есть похожие описания доначистить счет
        if similarity >= 0.20:
            final_score += 0.1

        logger.debug(
            "Итоговая оценка: %.3f, порог: %.3f",
            final_score,
            self.second_threshold
        )


        if final_score >= self.second_threshold:
            logger.info(
                "Описание принято: "
                "final=%.3f",
                final_score,
            )
            return True

        if not self.use_first_order:
            logger.warning(
                "Описание отклонено: "
                "second_score ниже порога и first_order отключён. "
                "second=%.3f threshold=%.3f text='%s'",
                second,
                self.second_threshold,
                normalized,
            )
            return False

        first = self.score_first(text)

        logger.debug(
            "Проверка первого порядка после отказа второго: "
            "first=%.3f threshold=%.3f",
            first,
            self.first_threshold,
        )

        if first >= self.first_threshold:

            logger.info(
                "Описание принято по модели первого порядка: "
                "score=%.3f threshold=%.3f",
                first,
                self.first_threshold,
            )

            return True


        logger.warning(
            "Описание отклонено: "
            "second=%.3f (< %.3f), "
            "first=%.3f (< %.3f), "
            "words=%d, text='%s'",
            second,
            self.second_threshold,
            first,
            self.first_threshold,
            len(normalized.split()),
            normalized,
        )


        return False
