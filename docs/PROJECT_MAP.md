# Saturnum Project Map

Saturnum coordinates a local workspace containing embedded component snapshots. The five repositories in the portfolio serve different purposes; they are not five copies of the same application.

| Repository | Role | Relationship to Saturnum |
| --- | --- | --- |
| [Saturnum](https://github.com/sablepushkar/Saturnum) | Workspace commands and orchestration | Holds embedded component snapshots and workspace-level checks. |
| [Acoustic-B-Box](https://github.com/sablepushkar/Acoustic-B-Box) | Audio-based emergency-message prototype | Standalone component home; its embedded copy is not auto-synced. |
| [VIREON](https://github.com/sablepushkar/vireon) | Synthetic pharmaceutical-style event system | Standalone component home; its embedded copy is not auto-synced. |
| [MedFindr](https://github.com/sablepushkar/MedFindr) | Healthcare/pharmaceutical discovery prototype | Independent project, not a Saturnum component. |
| [Consulting Analytics Lab](https://github.com/sablepushkar/consulting-analytics-lab) | Analytics and data-quality exercises | Independent project, not a Saturnum component. |

## Change workflow

1. Make and test component changes in that component's standalone repository.
2. Compare the tested source with Saturnum's embedded snapshot.
3. Copy/sync only the intended, reviewed changes into `components/`.
4. Run standalone and workspace tests; inspect failures before merging.
5. Update this map only if the repository roles or synchronization approach changes.

This map documents the current arrangement; it does not claim automated synchronization, production deployment, or real-world validation.
