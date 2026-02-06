# Test Diagrams

Some introductory text.

## Simple Box (Unicode)

```
┌────────────────────────┐
│ Header                 │
├────────────────────────┤
│ Row 1                  │
│ Row 2 is longer content│
│ Short                  │
└────────────────────────┘
```

## Missing corners and short rules

```
┌─────────────┐
│ Content here│
├─────────────┤
│ More content│
└─────────────┘
```

## ASCII style box

```
+------------------------+
| Header                 |
+------------------------+
| Row 1                  |
| Row 2 is longer content|
| Short                  |
+------------------------+
```

## Multiple boxes in one block

```
┌──────────┐
│ Box A    │
│ Content  │
└──────────┘

┌────────────────┐
│ Box B          │
│ Different width│
└────────────────┘
```

## Box with inner junctions

```
┌──────┬──────┐
│ Left │ Right│
├──────┼──────┤
│ A    │ B    │
└──────┴──────┘
```

## Code block should be ignored

```python
def hello():
    print("world")
```

## Non-diagram code block should be ignored

```
This is just text.
No box-drawing chars here.
Just plain content in a code block.
```

## Ragged markdown table

| Name | Description | Status |
|---|---|---|
| Alpha | The first thing | Active |
| Beta | A second, longer item | Pending |
| C | Short | Done |
