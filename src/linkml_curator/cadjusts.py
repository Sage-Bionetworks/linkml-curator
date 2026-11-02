"""Cadjusts, or Curator adjustments: rewrites for how Curator behaves, applied to the schema the
LinkML model describes.

`generator.class_schema` builds a plain draft-07 schema, then runs each function in
CADJUSTS over it in place. Each one covers a single Curator behavior and comes out on its
own: delete it from CADJUSTS and regenerate the fixtures. To see whether one is still
needed, generate with `gen-curator --no-cadjusts`, bind that schema to a RecordSet in a test
project, and repeat the check its docstring describes. The functions don't depend on each
other's order.
"""

from collections.abc import Callable, Iterator

DECIMAL = r"^-?[0-9]*\.?[0-9]+$"
GRID_TEXT = {"integer": {"pattern": r"^-?[0-9]+$"}, "number": {"pattern": DECIMAL},
             "boolean": {"enum": ["false", "true"]}}
"""What a value of each JSON type looks like as the text the grid holds."""
NON_BLANK = r"\S"


def _values(schema: dict) -> Iterator[tuple[str, dict]]:
    """Each property's key and its single-value schema: the items of an array, else itself."""
    for key, prop in schema["properties"].items():
        yield key, prop["items"] if prop.get("type") == "array" else prop


def grid_text(schema: dict) -> None:
    """Write numbers and booleans as text.

    Curator's grid loads a RecordSet's cells as text, whatever the bound schema says, so a
    number field holds "49" and a number or boolean type flags every row. Numbers become
    strings with a digit pattern and booleans the strings "true" and "false". A string can't
    carry `minimum` or `maximum`, so they are dropped.

    Check: fill a number column with valid values; every row is flagged while this is needed.
    """
    for _, value in _values(schema):
        if form := GRID_TEXT.get(value.get("type")):
            value.pop("minimum", None)
            value.pop("maximum", None)
            value.update(type="string", **form)


def non_blank_required(schema: dict) -> None:
    """Require a non-blank character in required text.

    The grid stores a blank text cell as "" and a blank list cell as [""], and `required`
    accepts both. A required string, or each item of a required list, gets the pattern \\S
    unless it already has a pattern or a fixed set of values.

    Check: leave a required text cell blank; it passes validation while this is needed.
    """
    for key, value in _values(schema):
        if (key in schema["required"] and value.get("type") == "string"
                and not value.keys() & {"pattern", "enum", "oneOf"}):
            value["pattern"] = NON_BLANK


CADJUSTS: tuple[Callable[[dict], None], ...] = (grid_text, non_blank_required)
