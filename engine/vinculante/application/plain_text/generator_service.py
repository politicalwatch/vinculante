from tqdm import tqdm

from .prompts import PLAIN_TEXT_PROMPT


class PlainTextGeneratorService:
    def __init__(self, section_repo, llm, batch_size: int = 20):
        self._repo = section_repo
        self._llm = llm
        self._batch_size = batch_size

    def generate(self, target_id: int | None = None, force: bool = False) -> int:
        sections = (
            self._repo.get_by_target(target_id)
            if target_id is not None
            else self._repo.get_all()
        )
        if not force:
            sections = [s for s in sections if s.plain_text is None or s.plain_text == s.text]

        count = 0
        for i in tqdm(range(0, len(sections), self._batch_size), desc="plain-text", unit="batch"):
            batch = sections[i : i + self._batch_size]
            for s in batch:
                prior = s.plain_text
                result = self._llm.invoke(PLAIN_TEXT_PROMPT.format(text=s.text))
                s.plain_text = result.content.strip()
                if s.plain_text != prior:
                    s.embedding = None
            self._repo.bulk_save(batch)
            count += len(batch)
        return count
