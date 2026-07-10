# Minimal Implementation: Domain-Specific Patterns

The principle: implement exactly what the test requires, nothing more. Domain specifics:

## Math Functions: Direct Formula

```python
# Test: assert calculate_discount(100, 10) == 90

# Minimal [x]
def calculate_discount(price, discount_percent):
    return price * (1 - discount_percent / 100)
```

```python
# NOT [x] (adds validation not yet tested)
def calculate_discount(price, discount_percent):
    if price < 0:
        raise ValueError("Price must be >= 0")
    return price * (1 - discount_percent / 100)
```

When the validation test arrives (later), add it then.

## Validation Functions: Simple Boolean Check

```python
# Test: assert validator.validate_email("x@y.com") == True

# Minimal [x]
def validate_email(self, email):
    return '@' in email
```

```python
# NOT [x] (adds regex not yet tested)
def validate_email(self, email):
    import re
    return bool(re.match(r'^[^@]+@[^@]+\.[^@]+$', email))
```

When the RFC-compliance test arrives (later), add it then.

## Parsing / String Processing: Iterate As Needed

```python
# Test: assert parse("a,b,c") == ["a", "b", "c"]

# Minimal [x] (iteration is necessary to pass this test)
def parse(self, line):
    return line.split(',')
```

```python
# Later test: assert parse("a,b\nc,d") handles newlines
# Minimal at this point [x]
def parse(self, data):
    return [line.split(',') for line in data.split('\n')]
```

Each feature gets its own test and minimal implementation.

## Classes: Extract Helpers Only On Duplication

```python
# Test 1: assert validator.validate_email() == True
# Minimal [x]
class UserValidator:
    def validate_email(self, email):
        return '@' in email
```

```python
# Test 2: assert validator.validate_password() == True
# Minimal [x] (no helper extracted yet — each method is called once)
class UserValidator:
    def validate_email(self, email):
        return '@' in email
    def validate_password(self, pwd):
        return len(pwd) >= 8
```

```python
# Test 3: assert combined validation (if you notice same logic 2+ times)
# NOW extract [x]
def _contains_required_character(self, text, char):
    return char in text
```

Wait until actual duplication appears; don't "just in case" extract.

## The Pattern

| Domain     | Minimal approach                           | Add more when...                      |
| ---------- | ------------------------------------------ | ------------------------------------- |
| Math       | Direct formula                             | Validation test arrives               |
| Validation | Simplest check that passes the assertion   | More specific validation test arrives |
| Parsing    | Split/iterate only as required by the test | Multi-line/edge case test arrives     |
| Classes    | Each method standalone, no helpers         | Same logic appears in 2+ methods      |
