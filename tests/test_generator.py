"""Shapes the NAMhub fixture doesn't exercise."""

import pytest
from linkml_runtime import SchemaView

from linkml_curator.cadjusts import grid_text, non_blank_required
from linkml_curator.generator import class_schema, template_classes

SCHEMA = """
id: https://example.org/probe
name: probe
imports: [linkml:types]
prefixes: {linkml: https://w3id.org/linkml/}
default_range: string
enums:
  Color:
    permissible_values:
      red: {description: The red one.}
      Blue:
      sea_green: {title: Sea Green}
  Size:
    permissible_values:
      sm: {title: Small}
      large:
slots:
  nodesc: {}
  bounded: {range: integer, minimum_value: 1, maximum_value: 10}
  counts: {range: float, multivalued: true}
  colors: {range: Color, multivalued: true}
  snake_case_name: {pattern: "^a", multivalued: true}
  size: {range: Size}
  fancy: {title: Very Fancy}
  flag: {range: boolean}
  needed: {required: true}
  needed_list: {required: true, multivalued: true}
  needed_code: {required: true, pattern: "^[A-Z]+$"}
  needed_count: {required: true, range: integer}
classes:
  Base: {abstract: true, slots: [nodesc]}
  Probe:
    is_a: Base
    slots: [bounded, counts, colors, snake_case_name, size, fancy, flag, needed, needed_list,
            needed_code, needed_count]
"""


def props(**kwargs) -> dict:
    return class_schema(SchemaView(SCHEMA), "Probe", **kwargs)["properties"]


def test_abstract_classes_are_not_templates():
    assert template_classes(SchemaView(SCHEMA)) == ["Probe"]


def test_inherited_slot_without_description():
    assert props()["Nodesc"] == {"title": "Nodesc", "type": "string"}


def test_without_cadjusts_types_and_bounds_are_kept():
    p = props(cadjusts=())
    assert p["Bounded"] == {"title": "Bounded", "type": "integer", "minimum": 1, "maximum": 10}
    assert p["Counts"]["items"] == {"type": "number"}
    assert p["Flag"] == {"title": "Flag", "type": "boolean"}
    assert p["Needed"] == {"title": "Needed", "type": "string"}


def test_grid_text_writes_numbers_and_booleans_as_strings():
    p = props(cadjusts=(grid_text,))
    assert p["Bounded"] == {"title": "Bounded", "type": "string", "pattern": "^-?[0-9]+$"}
    assert p["Counts"]["items"] == {"type": "string", "pattern": r"^-?[0-9]*\.?[0-9]+$"}
    assert p["Flag"] == {"title": "Flag", "type": "string", "enum": ["false", "true"]}


def test_non_blank_required_patterns_required_text():
    p = props(cadjusts=(non_blank_required,))
    assert p["Needed"]["pattern"] == r"\S"
    assert p["NeededList"]["items"] == {"type": "string", "pattern": r"\S"}
    assert p["NeededCode"]["pattern"] == "^[A-Z]+$"
    assert "pattern" not in p["Fancy"]
    assert "pattern" not in p["NeededCount"]


def test_cadjusts_do_not_depend_on_order():
    forward = props(cadjusts=(grid_text, non_blank_required))
    assert forward == props(cadjusts=(non_blank_required, grid_text))
    assert forward["NeededCount"]["pattern"] == "^-?[0-9]+$"


def test_multivalued_values_are_arrays():
    p = props()
    assert p["Counts"]["items"] == {"type": "string", "pattern": r"^-?[0-9]*\.?[0-9]+$"}
    assert p["SnakeCaseName"] == {
        "title": "Snake_case_name", "type": "array", "items": {"type": "string", "pattern": "^a"}
    }
    assert p["Colors"]["items"] == {"type": "string", "oneOf": [
        {"const": "Blue", "title": "Blue"},
        {"const": "Sea Green", "title": "Sea Green"},
        {"const": "red", "title": "red", "description": "The red one."},
    ]}


def test_enum_value_title_is_the_value():
    assert props()["Size"] == {"title": "Size", "enum": ["Small", "large"]}


def test_linkml_title_wins():
    assert props()["Fancy"]["title"] == "Very Fancy"


@pytest.mark.parametrize("slot, message", [
    ("{range: integer, pattern: '^1'}", "pattern .* string range, .* 'integer' is a number"),
    ("{minimum_value: 1}", "minimum_value .* needs a number range, but its range 'string'"),
    ("{range: Color, maximum_value: 3}", "maximum_value .* is an enum"),
])
def test_constraints_must_fit_the_type(slot, message):
    schema = SCHEMA.replace("fancy: {title: Very Fancy}", f"fancy: {slot}")
    with pytest.raises(ValueError, match=f"Slot 'fancy' sets {message}"):
        class_schema(SchemaView(schema), "Probe")
