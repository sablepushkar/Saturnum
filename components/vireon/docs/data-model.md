# VIREON data model

The current model is intentionally small and is used with synthetic examples.

- PharmaEvent: a validated event record with a timestamp and event fields.
- Signal: a rule-generated result linked to the event that triggered it.
- Evidence reference: a pointer to the source event, rule or manifest associated with a result.
- Audit record: a local record of selected changes or actions.
- Registry entry: metadata about a data, model or detector version.

The SQLite database is for local development. These objects do not represent a complete regulated data model, and the records are not a compliance guarantee.
