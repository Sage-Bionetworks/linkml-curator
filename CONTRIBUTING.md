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

### Cadjusts are kept apart

`class_schema` builds the schema the LinkML model describes, with `integer`, `number` and `boolean` types and their bounds. Rewrites for how Curator behaves today, called cadjusts (Curator adjustments), live in `src/linkml_curator/cadjusts.py`, one function per behavior, and run over that schema in the order of `CADJUSTS`. Each function's docstring says what Curator does and how to check whether it still does; `gen-curator --no-cadjusts` generates the schema to check with.
A rewrite that Curator no longer needs comes out by deleting it from `CADJUSTS`, deleting its test in `tests/test_generator.py`, and regenerating `tests/fixtures/expected/`. A new one is a function in the same module with its own test. Cadjusts must not depend on each other's order, which `test_cadjusts_do_not_depend_on_order` checks.
Keep `range: integer` and the bounds in a model even while `grid_text` writes numbers as text, for what they mean and for when it comes out.

### Enum values with descriptions become `oneOf`

Curator's forms are rendered by
[react-jsonschema-form](https://github.com/rjsf-team/react-jsonschema-form), which reads a
value's title and description only from `oneOf` entries that have a `const`. An enum whose
values have no descriptions stays a plain `enum`.
