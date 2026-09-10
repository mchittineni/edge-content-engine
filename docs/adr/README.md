# Architecture Decision Records

An ADR records a decision that was **hard to reverse**, **surprising without context**,
and involved a **real trade-off**. If a change fails any of those three tests, it belongs
in a commit message or a code comment — not here.

## Process

1. Copy `0000-template.md` to `NNNN-short-title.md` (next free number).
2. Open it as `Proposed` in the pull request that implements the decision.
3. Merge it as `Accepted` alongside the change it describes.
4. Never edit an accepted ADR's decision. Supersede it with a new one and link both.

## Index

| ADR | Title | Status |
| --- | --- | --- |
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-stateless-agents-with-job-contracts.md) | Stateless agents coordinated by JobContract | Accepted |
| [0003](0003-content-lake-storage-abstraction.md) | Filesystem/S3 content lake behind one abstraction | Accepted |
| [0004](0004-enforced-quality-gates.md) | Enforced, non-bypassable quality gates | Accepted |
| [0005](0005-pin-all-supply-chain-inputs.md) | Pin every supply-chain input by digest | Accepted |
