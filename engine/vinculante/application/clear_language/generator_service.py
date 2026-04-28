from tqdm import tqdm

from .prompts import CLEAR_LANGUAGE_PROMPT


class ClearLanguageGeneratorService:
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
            sections = [s for s in sections if s.clear_language is None or s.clear_language == s.text]

        count = 0
        for i in tqdm(range(0, len(sections), self._batch_size), desc="clear-language", unit="batch"):
            batch = sections[i : i + self._batch_size]
            for s in batch:
                prior = s.clear_language
                result = self._llm.invoke(CLEAR_LANGUAGE_PROMPT.format(text=s.text))
                s.clear_language = result.content.strip()
                if s.clear_language != prior:
                    s.embedding = None
            self._repo.bulk_save(batch)
            count += len(batch)
        return count
