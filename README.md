# nldate

`nldate` parses common English date expressions into `datetime.date` objects.

```python
from datetime import date
from nldate import parse

assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)
assert parse("next Tuesday", today=date(2026, 5, 14)) == date(2026, 5, 19)
```

