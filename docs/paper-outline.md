# FusionFlow Research Paper — Outline

**Working title:** *FusionFlow: A Temporal Specification Language for Reproducible ML Experimentation.*

**Target venue:** arXiv (preprint) → systems venue (MLSys, EuroSys workshop, or HCOMP).

**Status:** outline only. Drafting begins after v0.5.0-dev0 stabilizes.

## Abstract (180 words target)

We present FusionFlow, a domain-specific language and runtime for describing, versioning, and reasoning about machine-learning experiments as **temporal specifications** rather than scripts. A FusionFlow `.ff` source compiles to a deterministic Temporal IR (JSON) that is the contract between language frontends and execution backends. Time is first-class: datasets carry versions, pipelines reference dataset versions, timelines branch and merge with explicit justifications. The runtime currently ships a Pandas backend and consumes IR-only — no AST imports — so future backends (Spark, Polars) plug in without source-level changes. We demonstrate reproducibility (byte-identical run outputs across processes given a seed), additive evolution (v0.3 specs parse unmodified in v0.4), and semantic diffability (`fusionflow diff` operates on IR structure, not source text). We argue this design transposes the version-control discipline of code to the experimentation discipline of ML.

## Sections

1. **Introduction** — the reproducibility crisis in ML; existing tools (MLflow, DVC, W&B) record artifacts but don't language-ify intent. FusionFlow's position.
2. **Temporal Specification Semantics** — formal definitions of dataset/pipeline/model/experiment/timeline/merge. Why time as a first-class noun.
3. **IR Design** — the JSON schema, the contract, additive evolution, version gating, determinism guarantees.
4. **Semantic Merge** — conflict detection across datasets/pipelines/models/experiments. `prefer_metrics` strategy. Why this is harder than git's textual merge.
5. **Execution** — IR → ExecutionPlan → Backend. Why backends consume IR-only. The Pandas backend; the planned Spark backend.
6. **Provenance** — lineage tracking via dataset references; merge justifications as audit log.
7. **Comparison to related work** — MLflow (artifacts), DVC (pipelines as code), Pachyderm (data versioning), Hopsworks, ZenML.
8. **Evaluation** — reproducibility experiment (cross-machine determinism), expressiveness study (rewrite N existing ML scripts as `.ff`), case study (timeline merge on a real classification task).
9. **Limitations and future work** — frozen IR shape commitments, plugin API, online learning hooks, distributed execution.

## Artifacts to ship alongside

- Reproducibility appendix: `fusionflow certify run.json` (v1.0 feature).
- Companion repo with all paper figures' source `.ff` files.
- Docker image with pinned `pandas` + `sklearn` for the cross-machine determinism claim.

## Open questions for drafting

- Position as **language** paper (cite Brooks "No Silver Bullet," Coplien on DSLs) or **systems** paper (cite Pachyderm, DVC)?
- How much formalism? Provide operational semantics for merge, or stay informal?
- One case study or three?
