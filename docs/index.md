# FusionFlow

**A Temporal Specification Language (TSL) for Machine Learning Experimentation.**

FusionFlow is a domain-specific language for describing, versioning, and reasoning about ML experiments over time. A `.ff` file is not a script and not a config file — it is a *temporal contract* for reproducible experimentation.

## Install

```bash
pip install fusionflow
```

For the full experience:

```bash
pip install "fusionflow[mlflow,jupyter]"
```

## A 30-second tour

Write a spec:

```fusionflow
dataset customers v1
    source "customers.csv"
end

pipeline churn_pipe
    from customers v1
    features [age, income, spend]
    split 0.7
    target churned
end

model rf
    type random_forest_classifier
    params { trees: 50, max_depth: 5 }
end

experiment churn_baseline
    uses pipeline churn_pipe
    uses model rf
    metrics [accuracy, f1]
end
```

Run it:

```bash
fusionflow run churn.ff --backend pandas --seed 42
```

Diff two versions semantically:

```bash
fusionflow diff churn.ff churn_v2.ff
```

Visualize the experiment graph:

```bash
fusionflow visualize churn.ff --format html --out report.html
```

## Why FusionFlow

- **Time is first-class.** Datasets carry versions; timelines branch and merge with justifications.
- **The IR is the contract.** `.ff` compiles to a deterministic JSON IR. Backends consume IR only — so the language evolves without breaking execution.
- **Determinism.** Same seed + same data = byte-identical results, verified across processes.
- **Semantic diff and merge.** Compare and combine experiments by structure, not by text.

## Where to go next

- **[Getting Started](getting-started.md)** — install to first run in 5 minutes
- **[CLI Reference](cli.md)** — every subcommand and flag
- **[IR Specification](ir-spec-v0.4.md)** — the Temporal IR contract
- **[Backends](backends.md)** — the Pandas backend and how to write your own

## Project status

FusionFlow is at **v0.5.0-dev0**. The grammar is frozen for the v0.5 cycle. See the
[GitHub repository](https://github.com/Dinesh0401/fusionflow) for the roadmap, contribution
guide, and design principles.
