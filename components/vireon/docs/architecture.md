# VIREON Advanced — Architecture

I am keeping VIREON as a set of small modules with clear boundaries. The first versions are intentionally simple so each part can be tested before adding streaming infrastructure, advanced statistics, or external services.

## Main flow

synthetic source
      |
      v
event validation
      |
      v
SQLite event store
      |
      +------------------+
      |                  |
      v                  v
signal engine        quality / model checks
      |                  |
      v                  v
signal + evidence     review flags
      |                  |
      +--------+---------+
               |
               v
        evidence graph
               |
               v
      trial / lifecycle view
               |
               v
          human review

The point is not that every real drug-development platform would use exactly this layout. The point is that the important controls are visible instead of being hidden inside one large service.

## Module boundaries

### Event boundary

core/models.py defines the basic event, signal, and evidence objects.

core/validation.py checks identifiers, required fields, timezone-aware timestamps, future timestamps, empty lab/vital payloads, and non-finite numeric values.

### Signal engine

signal_engine.py contains small deterministic rules with an explicit detector version.

That makes a detection reproducible and leaves room for a later statistical or ML detector without changing the rest of the system contract.

### Storage

storage/sqlite.py stores events, signals, evidence links, and audit records.

Foreign keys and application-level checks keep the basic provenance chain connected.

### Evidence graph

evidence_graph.py turns persisted event/signal/evidence relationships into a serializable graph:

event -> signal -> evidence

The graph is kept separate from the storage implementation so a graph database can be added later without rewriting the domain objects.

### AI-GUARD

ai_guard.py is a monitoring component, not a model-deployment service.

It records context of use, risk tier, validation status, reference/current sample summaries, and monitoring flags for mean shift, variance shift, and missingness.

A flag means review in this prototype. It is not a clinical conclusion.

### Digital measures

digital_measures.py checks completeness, missingness, finite numeric values, and expected minimum/maximum ranges.

The result is an engineering review signal, not a validation claim for a real device.

### Trial integrity

trial_integrity.py works at site level and reports indicators such as missingness patterns, protocol-deviation patterns, timestamp collisions, and duplicate event IDs.

These are monitoring indicators. They are not fraud findings.

### Lifecycle

lifecycle.py represents a candidate moving through discovery, preclinical, clinical phases, regulatory, manufacturing, and post-market stages.

The module connects the other controls to a lifecycle view. It does not predict approval or make regulatory decisions.

### Interoperability

interop.py provides small FHIR Observation and OMOP-shaped projections.

Local synthetic fields are deliberately not presented as fully mapped clinical terminology. That mapping remains a separate problem.

## Storage and provenance rules

A signal can only be stored for an existing event.

An evidence link can only be stored for an existing signal, and its event ID must match the event attached to that signal.

Create/update/link operations leave audit records.

The resulting prototype trace is:

source event -> detection -> evidence -> audit

## What is deliberately not here yet

There is no message broker, distributed event bus, real clinical-data connector, graph database, terminology service, automated clinical decision system, or regulatory submission system. A lightweight local registry and evidence-manifest generator exist, but they are prototype components rather than governed production services.

Those are later architecture layers. I do not want to fake them inside a small prototype.

## Design direction

The long-term direction is to replace individual in-process components with deployable services while keeping the same domain contracts.

If development resumes, the next engineering layer should prioritize event idempotency, stronger statistical monitoring, explicit terminology mapping, and deployment/observability only after the current local workflows remain stable.
