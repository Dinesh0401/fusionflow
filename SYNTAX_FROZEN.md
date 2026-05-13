# Syntax Freeze — v0.5 cycle

**The FusionFlow `.ff` grammar is frozen for the v0.5 cycle.**

## What's frozen

- All keywords: `dataset`, `pipeline`, `model`, `experiment`, `timeline`, `merge`, `from`, `derive`, `select`, `target`, `extend`, `source`, `schema`, `description`, `type`, `params`, `uses`, `metrics`, `into`, `because`, `strategy`, `end`, `and`, `or`, `not`, `where`, `split`, `features`, `checkpoint`.
- All top-level construct shapes (dataset/pipeline/model/experiment/timeline/merge).
- Expression precedence and associativity.
- Operator vocabulary.

## What may still change in v0.5

- The `join` keyword (new — additive, won't break existing files).
- IR shape additions (additive, gated by `ir_version`).
- New strategies for `merge ... strategy <name>` (additive).

## What's explicitly off-limits until v0.6+

- Renaming existing keywords.
- Removing keywords.
- Changing operator precedence.
- Breaking the additive contract.

## Rationale

The project has crossed from "experiment" to "real OSS systems project." Adopters need a stable target. Syntax churn breaks examples, docs, and contributor velocity.

## When does the freeze lift?

When v0.6 begins. Any breaking change requires a major version bump and migration notes in `RELEASE_NOTES.md`.
