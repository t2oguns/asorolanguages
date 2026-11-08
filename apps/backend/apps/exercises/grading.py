"""Pure graders: normalized input -> score and evidence for learning targets."""
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass

from django.core.exceptions import ValidationError


def normalize(text, policy):
    text = unicodedata.normalize("NFC", text)
    if not policy["case_sensitive"]:
        text = text.casefold()
    if policy["ignore_diacritics"]:
        text = "".join(char for char in unicodedata.normalize("NFD", text) if unicodedata.category(char) != "Mn")
    if policy["ignore_punctuation"]:
        text = "".join(char for char in text if not unicodedata.category(char).startswith("P"))
    return " ".join(unicodedata.normalize("NFC", text).split())


@dataclass(frozen=True)
class Grade:
    score: float
    feedback: str
    target_results: list


def _text_score(response, answers, policy):
    if not isinstance(response, str):
        raise ValidationError("Submit a text answer.")
    return float(normalize(response, policy) in {normalize(answer, policy) for answer in answers})


def grade_exercise(exercise, response):
    """Grade the same Exercise-shaped data delivered to Next.js."""
    kind = exercise["exercise_type"]
    policy = exercise
    evidence = defaultdict(list)
    if kind == "multiple_choice":
        if not isinstance(response, list) or any(not isinstance(value, str) for value in response):
            raise ValidationError("Submit a list of option IDs.")
        options = exercise["options"]
        if len(set(response)) != len(response) or not set(response) <= {row["id"] for row in options}:
            raise ValidationError("Unknown or duplicate choice IDs.")
        score = float(set(response) == {row["id"] for row in options if row["is_correct"]})
    elif kind in {"translation", "error_correction", "word_order"}:
        answers = sorted(exercise["accepted_answers"], key=lambda row: (not row["is_primary"], row["id"]))
        if kind == "word_order":
            tiles = answers[0]["text"].split()
            if (not isinstance(response, list) or any(not isinstance(value, str) for value in response)
                    or Counter(response) != Counter(tiles)):
                raise ValidationError("Use each supplied word tile exactly once.")
            response = " ".join(response)
        score = _text_score(response, [row["text"] for row in answers], policy)
    elif kind in {"fill_blank", "matching"}:
        rows = exercise["fill_blank_slots"] if kind == "fill_blank" else exercise["matching_pairs"]
        if not isinstance(response, dict) or set(response) != {row["id"] for row in rows}:
            raise ValidationError("Submit one answer for every blank or matching item.")
        if kind == "matching":
            values = list(response.values())
            if (any(not isinstance(value, str) for value in values)
                    or len(set(values)) != len(values) or set(values) != {row["id"] for row in rows}):
                raise ValidationError("Match each right-hand item exactly once.")
        scores = []
        for row in rows:
            item_score = (_text_score(response[row["id"]], [answer["text"] for answer in row["accepted_answers"]], policy)
                          if kind == "fill_blank" else float(response[row["id"]] == row["id"]))
            scores.append(item_score)
            target_id = row["target_id"] or exercise["targets"][0]["id"]
            evidence[target_id].append(item_score)
        score = sum(scores) / len(scores)
    else:
        raise ValidationError("Unsupported exercise type.")
    results = []
    for target in exercise["targets"]:
        values = evidence.get(target["id"], []) if kind in {"fill_blank", "matching"} else [score]
        if values:
            results.append({**target, "score": sum(values) / len(values)})
    return Grade(score, "Correct." if score == 1 else "Review the answer and try again.", results)
