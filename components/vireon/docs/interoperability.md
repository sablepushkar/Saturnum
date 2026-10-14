# Interoperability

VIREON includes intentionally small FHIR and OMOP boundary demonstrations.

## FHIR

GET /v1/interop/fhir/events/{event_id} returns an illustrative FHIR Observation. FHIR R4 defines Observation as a resource for measurements and simple assertions about a patient, device or other subject. VIREON only demonstrates the mapping boundary; it does not implement full terminology, profiles, validation or conformance.

## OMOP

GET /v1/interop/omop/events/{event_id} returns an illustrative measurement mapping. Local synthetic keys are deliberately marked as unmapped rather than pretending they are validated vocabulary concepts.

These endpoints are portfolio demonstrations of where standards-aware adapters would sit in a larger system.
