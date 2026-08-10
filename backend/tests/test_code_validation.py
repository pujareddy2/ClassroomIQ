"""
Unit tests for modular CodeValidator under app/services/validation/validators/
"""

from app.services.validation.validators.code_validator import CodeValidator
from app.services.validation.validation_models import ValidationCategory, ValidationStatus, ValidationType


def test_code_validator_python2_print():
    text = "In Python we print output like print 'Hello World'"
    res = CodeValidator.validate(text)
    assert res is not None
    cat, status, v_type, severity, reason, score = res
    assert cat == ValidationCategory.CODE
    assert status == ValidationStatus.INCORRECT
    assert v_type == ValidationType.INCORRECT_CODE
    assert "Python 3" in reason


def test_code_validator_java_array_length():
    text = "To get the size of an array in Java, we call array.length()"
    res = CodeValidator.validate(text)
    assert res is not None
    cat, status, v_type, severity, reason, score = res
    assert cat == ValidationCategory.CODE
    assert status == ValidationStatus.INCORRECT
    assert "Java" in reason


def test_code_validator_valid_code():
    text = "In Python 3 we use print('Hello World') with parentheses."
    res = CodeValidator.validate(text)
    assert res is None
