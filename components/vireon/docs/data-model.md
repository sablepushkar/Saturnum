# VIREON Data Model

VIREON keeps the portfolio model deliberately small.

- PharmaEvent: validated timestamped input from a synthetic source.
- Signal: deterministic finding generated from an event and a detector version.
- EvidenceLink: provenance edge connecting a signal to its source event.
- Audit record: append-style record of storage actions.
- EvidenceManifest: reproducibility snapshot of dataset, detector, inputs, signals and evidence.
- RegistryItem: versioned metadata for models, datasets, detectors or measures.

The intended lineage is:

Event -> Signal -> Evidence -> Manifest -> Review

The model is not a clinical data model and does not claim terminology or regulatory conformance.
