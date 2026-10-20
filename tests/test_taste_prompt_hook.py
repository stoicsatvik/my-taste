import importlib.util
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "hooks" / "taste_prompt.py"
spec = importlib.util.spec_from_file_location("taste_prompt", p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_explicit_preference_activates_save_guidance():
    assert "save concise evidence" in module.guidance("I hate this corporate style.")


def test_creative_work_retrieves_taste():
    assert "taste_brief" in module.guidance("Design a landing page for a cafe")


def test_unrelated_technical_task_is_ignored():
    assert module.guidance("Fix this SQL query") is None


def test_passive_usage_is_not_inferred_as_preference():
    assert module.guidance("I used the generated code yesterday") is None


def test_empty_and_oversized_inputs_are_ignored():
    assert module.guidance("") is None
    assert module.guidance("x" * 12001) is None
