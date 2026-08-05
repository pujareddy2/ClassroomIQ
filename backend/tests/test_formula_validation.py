"""
Unit tests for modular FormulaValidator under app/services/validation/validators/
"""

from app.services.validation.validators.formula_validator import FormulaValidator
from app.services.validation.validation_models import ValidationCategory, ValidationStatus, ValidationType


def test_formula_validator_incorrect_big_o():
    text = "Bubble sort has an average time complexity of O(1)."
    res = FormulaValidator.validate(text)
    assert res is not None
    cat, status, v_type, severity, reason, score = res
    assert cat == ValidationCategory.FORMULA
    assert status == ValidationStatus.INCORRECT
    assert v_type == ValidationType.INCORRECT_FORMULA
    assert "Bubble Sort" in reason
    assert score >= 90.0


def test_formula_validator_incorrect_equation():
    text = "According to mass energy equivalence E = mc^3."
    res = FormulaValidator.validate(text)
    assert res is not None
    cat, status, v_type, severity, reason, score = res
    assert cat == ValidationCategory.FORMULA
    assert status == ValidationStatus.INCORRECT
    assert "mc^2" in reason


def test_formula_validator_valid_text_returns_none():
    text = "Linear search takes O(n) time complexity in worst case."
    res = FormulaValidator.validate(text)
    assert res is None
