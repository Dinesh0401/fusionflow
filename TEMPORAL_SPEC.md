# FusionFlow Temporal Specification Language

FusionFlow `.ff` files describe machine-learning experiments as temporal specifications rather than executable scripts. Each file acts as an immutable contract that captures what data, transformations, models, and timelines exist, why branches differ, and how merges should be justified.

## Core Ideas

- **Immutable experiment history:** Every declaration is append-only. Branches extend earlier state instead of mutating it.
- **Backend independent:** `.ff` files never contain execution logic. They compile to an intermediate representation that backends can replay deterministically.
- **Auditable merges:** Integrating timeline results requires documented justification and explicit merge strategies.

## Language Surface

### Datasets

```
dataset customers v1
    description "Baseline churn cohort"
    source "s3://ml-bucket/customers.csv"
    schema {
        id: int
        age: int
        tenure: int
        churned: bool
    }
end
```

Datasets are versioned declarations. Schemas make drift reviewable before execution.

### Pipelines

```
pipeline churn_features
    from customers v1
    derive spend_per_day = amount / days
    select [spend_per_day, age, tenure]
    target churned
end
```

Pipelines are pure transformations: no side effects, no I/O, and no randomness.

### Models

```
model rf_v1
    type random_forest
    params {
        trees: 200
        depth: 8
    }
end
```

Models bind hyperparameters separately from pipelines to keep feature engineering reproducible.

### Experiments

```
experiment churn_baseline
    uses pipeline churn_features
    uses model rf_v1
    metrics [accuracy, f1]
end
```

Experiments connect pipelines and models and declare the evaluation metrics that matter for promotion.

Optional `extend { ... }` blocks allow on-branch derivations without mutating the base pipeline.

### Timelines and Merges

```
timeline v2 "Feature exploration"
    experiment churn_interaction
        uses pipeline churn_features
        uses model rf_v1
        metrics [accuracy, f1]
        extend {
            derive age_spend = age * spend_per_day
        }
    end
end

merge v2 into main
    because "Improved f1 by +4.2% without accuracy loss"
    strategy prefer_metrics f1
end
```

Timelines stage experiments in isolation. Merges require a human-readable justification plus a merge strategy that tooling can enforce.

## Execution Model

1. **Parse:** The lexer and parser convert `.ff` files into AST nodes (`DatasetDeclaration`, `PipelineDefinition`, `ModelDefinition`, `ExperimentDefinition`, `TimelineDefinition`, `MergeStatement`).
2. **Register:** The interpreter stores declarations in the runtime registry without executing any data processing.
3. **Compile:** Backends consume the temporal registry to materialize runs, compare metrics, or replay branches.

The runtime guarantees that experiments reference existing pipelines and models, datasets must exist before pipelines can bind to them, and merges only operate on known timelines.

## Repository Entry Points

| Concern | File |
| --- | --- |
| Token definitions | `fusionflow/tokens.py` |
| Lexer | `fusionflow/lexer.py` |
| AST nodes | `fusionflow/ast_nodes.py` |
| Parser | `fusionflow/parser.py` |
| Runtime registry | `fusionflow/runtime.py` |
| Spec interpreter | `fusionflow/interpreter.py` |
| Tests | `tests/` |

Use `pytest` to validate the language surface:

```
C:/Users/sjdin/fusionflow/.venv_prod/Scripts/python.exe -m pytest
```

`TEMPORAL_SPEC.md` stays canonical for the language design; downstream documentation should link back here when describing `.ff` semantics.
