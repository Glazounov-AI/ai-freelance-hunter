import re
from dataclasses import dataclass

from app.ai.profile import FreelancerProfile


@dataclass(frozen=True)
class Analysis:
    score: int
    matched_skills: tuple[str, ...]
    explanation: str
    warnings: tuple[str, ...]
    draft: str


def analyze_offline(title: str, description: str, profile: FreelancerProfile) -> Analysis:
    # Offline baseline is deterministic, not a substitute for semantic LLM evaluation.
    text = f"{title} {description}".casefold()
    matched = []
    for item in profile.evidence:
        term = item.skill.casefold()
        if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text):
            matched.append(item)
    score = min(100, len(matched) * 25)
    warnings = ["Оценка по ключевым словам, без семантического AI-анализа"]
    if not matched:
        warnings.append("Нет подтверждённых совпадений с профилем")
    evidence = "; ".join(
        f"{item.skill}: {item.proof.strip().rstrip('.!?…')}"
        for item in matched[:3]
    )
    explanation = (f"Найдено подтверждённых совпадений: {len(matched)}. "
                   + (evidence or "Релевантные навыки не установлены."))
    draft = (
        f"Здравствуйте! Ознакомился с задачей «{title[:180]}». "
        + (f"Мой релевантный опыт: {evidence}. " if evidence else
           "Для оценки соответствия мне нужно уточнить детали задачи. ")
        + "Могу обсудить требования, сроки и критерии результата. "
        + "Это черновик, требующий проверки перед отправкой."
    )
    return Analysis(score, tuple(item.skill for item in matched), explanation,
                    tuple(warnings), draft)
