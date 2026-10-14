# Architecture Decisions

## ADR-0001 — Synthetic data first
VIREON uses synthetic data for the portfolio release. This makes scenarios deterministic and avoids presenting the prototype as a clinical system.

## ADR-0002 — Deterministic signals before ML
The first detector is explicit and versioned. This makes behavior inspectable and testable before adding more complex analytical methods.

## ADR-0003 — Evidence lineage is a first-class object
Signals keep links to their source events and detector version. Evidence manifests make the inputs and outputs of a demonstration reproducible.

## ADR-0004 — Human review remains the boundary
AI-GUARD and monitoring modules surface review conditions; they do not issue treatment, diagnosis, safety, efficacy or regulatory decisions.
