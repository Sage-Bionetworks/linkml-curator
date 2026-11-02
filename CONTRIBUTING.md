# Contributing

Bug reports, questions and pull requests are welcome. Please open an
[issue](https://github.com/Sage-Bionetworks/linkml-curator/issues) before starting on a large
change, so we can agree on the approach first.

When reporting a problem with generated output, include the LinkML model (or a minimal slice
of it), the command you ran, and the JSON you expected.

## Development

The project uses [uv](https://docs.astral.sh/uv/) and supports Python 3.12 and later.

```bash
uv sync
uv run pytest
uv run ruff check
```

CI runs both checks on every pull request.

## Output snapshots

`tests/fixtures/namhub/` is the NAMhub model, and `tests/fixtures/expected/` is the
generator's output for it. A change to `expected/` is a change to the output, so a pull request
that changes it should say why. Regenerate the snapshot and review the diff:

```bash
uv run gen-curator tests/fixtures/namhub/namhub.yaml -d tests/fixtures/expected
```

Behavior the NAMhub model doesn't exercise is pinned in `tests/test_generator.py`. Each
`curator-lint` rule has a test in `tests/test_lint.py` on a small model that trips only that
rule; a new rule gets one of those.

## Design notes

Some of the generator's choices look arbitrary until you know what Synapse does with the output.

### The JSON is built directly from the LinkML model

synapseclient can generate Curator schemas itself, but only from its CSV data model, and one
display-label setting controls both enum values and property keys. It can't produce enum values
that keep their spaces (`Level 1`) alongside PascalCase keys (`DatasetAssay`), which Curator
needs. `gen-curator` writes the JSON from LinkML's SchemaView instead, so this project owns the
output shape. If Curator's expectations change, the generator has to change with them.

### Every value is a string

Curator's grid loads a RecordSet's cells as text, whatever the bound schema says, so a number field holds `"49"` and a `number` or `boolean` type would flag every row.
Numbers are written as strings with a digit pattern and booleans as the strings `true` and `false`. `minimum_value` and `maximum_value` can't be expressed on a string, so they are dropped. Keep `range: integer` in the model anyway, for what it means.

### Required text must be non-blank

The grid stores a blank text cell as `""` and a blank list cell as `[""]`, and `required` accepts both. A required string slot, or each item of a required list, gets the pattern `\S` unless the model gives it a pattern of its own.

### Enum values with descriptions become `oneOf`

Curator's forms are rendered by
[react-jsonschema-form](https://github.com/rjsf-team/react-jsonschema-form), which reads a
value's title and description only from `oneOf` entries that have a `const`. An enum whose
values have no descriptions stays a plain `enum`.
