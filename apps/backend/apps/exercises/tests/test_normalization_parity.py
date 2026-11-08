import json
from pathlib import Path

import pytest

from apps.exercises.grading import grade_exercise, normalize

CASES = json.loads((Path(__file__).resolve().parents[5] / "shared" / "grading-normalization.json").read_text())


@pytest.mark.parametrize("example", CASES, ids=lambda row: repr(row["text"]))
def test_normalization_matches_the_shared_frontend_contract(example):
    policy = {"case_sensitive": False, "ignore_punctuation": False, "ignore_diacritics": False, **example["policy"]}
    assert normalize(example["text"], policy) == example["expected"]


GRADING_CASES = json.loads((Path(__file__).resolve().parents[5] / "shared/grading-cases.json").read_text())


@pytest.mark.parametrize("example", GRADING_CASES, ids=lambda example: example["name"])
def test_shared_grading_cases(example):
    result = grade_exercise(example["exercise"], example["response"])
    assert result.score == pytest.approx(example["score"])
    assert [target["score"] for target in result.target_results] == pytest.approx(example["target_scores"])
