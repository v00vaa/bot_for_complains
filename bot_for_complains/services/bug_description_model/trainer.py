from pathlib import Path

from sqlalchemy import select

from database.models import BugData

from .markov import MarkovModel


async def train_bug_description_model(
    bug_description_model: MarkovModel,
    session,
    train_file: str,
):
    corpus: list[str] = []

    path = Path(train_file)

    if path.exists():
        with open(path, encoding="utf-8") as f:
            corpus.extend(
                line.strip()
                for line in f
                if line.strip()
            )

    result = await session.execute(
        select(BugData.description).where(
            BugData.is_training_sample.is_(True)
        )
    )

    corpus.extend(result.scalars().all())

    bug_description_model.fit(corpus)

    return bug_description_model

async def retrain_bug_description_model(
    bug_description_model: MarkovModel,
    session_factory,
    train_file: str,
):
    async with session_factory() as session:
        await train_bug_description_model(
            bug_description_model,
            session,
            train_file,
        )