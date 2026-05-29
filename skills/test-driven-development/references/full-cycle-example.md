# Concrete Example: Full RED-GREEN-REFACTOR Cycle

Here's what proper TDD looks like in practice, step by step.

## RED: Write First Test

```python
# discount.py (test file — written first)
def test_basic_discount():
    from discount_module import calculate_discount
    result = calculate_discount(100, 10)
    assert result == 90
```

Run: `pytest test_discount.py::test_basic_discount`
Result: `FAILED - ModuleNotFoundError: No module named 'discount_module'`

**Analysis**: Environment failure → create the module.

## GREEN: Minimal Implementation

```python
# discount_module.py (created now — minimal)
def calculate_discount(price, discount_percent):
    return price * (1 - discount_percent / 100)
```

Run: `pytest test_discount.py::test_basic_discount`
Result: `PASSED`

## REPEAT: Add Second Test

```python
# Back to test file
def test_zero_discount():
    from discount_module import calculate_discount
    result = calculate_discount(100, 0)
    assert result == 100
```

Run: `pytest test_discount.py`
Result: `PASSED` (already works with current implementation!)

## REPEAT: Add Edge Case Test

```python
def test_full_discount():
    from discount_module import calculate_discount
    result = calculate_discount(100, 100)
    assert result == 0
```

Run: `pytest test_discount.py`
Result: `PASSED` (formula handles this too!)

## REPEAT: Add Error Case Test

```python
def test_negative_price_raises_error():
    from discount_module import calculate_discount
    import pytest
    with pytest.raises(ValueError):
        calculate_discount(-50, 10)
```

Run: `pytest test_discount.py`
Result: `FAILED - AssertionError: ValueError not raised`

**Analysis**: Logic failure → add validation to implementation.

## GREEN: Enhance Implementation

```python
# discount_module.py (now with validation)
def calculate_discount(price, discount_percent):
    if price < 0:
        raise ValueError("Price must be >= 0")
    return price * (1 - discount_percent / 100)
```

Run: `pytest test_discount.py`
Result: `PASSED` (all 4 tests now pass)

## REFACTOR: All Tests GREEN, Now Improve Code

```python
# discount_module.py (refactored for clarity)
def calculate_discount(price, discount_percent):
    """Calculate discounted price.

    Args:
        price: Original price (must be >= 0)
        discount_percent: Discount percentage (0-100)

    Returns:
        Discounted price as float

    Raises:
        ValueError: If price < 0
    """
    if price < 0:
        raise ValueError("Price must be >= 0")
    discount_multiplier = 1 - (discount_percent / 100)
    return price * discount_multiplier
```

Run: `pytest test_discount.py`
Result: `PASSED` (all 4 tests still pass after refactoring)

## Cycle Summary

- ✅ Each test written before implementation (RED)
- ✅ Minimal code added to pass each test (GREEN)
- ✅ Tests run after each change (validation)
- ✅ Refactoring only after all tests GREEN
- ✅ One test = one decision point
