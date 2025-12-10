# FusionFlow

**A polyglot, provenance-aware pipeline language with first-class temporal branching**

FusionFlow is an experimental domain-specific language (DSL) for data transformation and machine learning pipelines. It combines:

- **Temporal Branching** — First-class language primitives for checkpoints, timelines, and what-if experiments
- **Unified Execution Graph (UPEG)** — Canonical intermediate representation with capability-aware backend planning
- **Provenance Tracking** — Column-level lineage for reproducible experiments
- **Polyglot Integration** — Seamless execution across Python (Pandas, scikit-learn) with future support for Spark/JVM and GPU backends

## ✨ Features

- **Python-like syntax** with domain-specific constructs for data pipelines
- **Checkpoint/Timeline semantics** for reproducible what-if experiments
- **Automatic ML model training** with built-in metrics
- **Copy-on-write state management** for efficient branching
- **VS Code syntax highlighting** (extension coming soon)

## 🚀 Installation

### Python Users
```bash
pip install fusionflow
```

### Windows Users (.exe - No Python Needed)
Download the latest `.exe` from [GitHub Releases](https://github.com/yourusername/fusionflow/releases)

### VS Code Users
Install the extension from VS Code Marketplace:
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search "FusionFlow"
4. Click Install

### From Source
```bash
cd fusionflow
pip install -e .
```

## 📖 Quick Start

Create a file `example.ff`:

```fusionflow
dataset customers from "data/customers.csv"

pipeline churn_features:
    from customers
    where active == 1
    derive spend_per_day = amount / days
    features [spend_per_day, age]
    target churned
    split 80% train, 20% test
end

experiment churn_exp:
    model random_forest
    using churn_features
    metrics [accuracy, f1]
end

print metrics of churn_exp
```

Run it:

```bash
fusionflow example.ff
```

## 🌟 Language Features

### Dataset Declaration

```fusionflow
dataset customers from "customers.csv"
dataset events from "events.parquet" versioned true
```

### Pipeline Definition

```fusionflow
pipeline my_pipeline:
    from customers
    join events on customers.id == events.user_id
    where age > 18
    derive total_spend = price * quantity
    features [age, total_spend, category]
    target purchased
    split 80% train, 20% test
end
```

### Experiments

```fusionflow
experiment my_experiment:
    model random_forest          # or: logistic_regression
    using my_pipeline
    metrics [accuracy, f1, precision, recall, auc]
end

print metrics of my_experiment
```

### Temporal Branching

```fusionflow
# Save checkpoint
checkpoint "baseline"

experiment baseline_exp:
    model random_forest
    using features_v1
    metrics [accuracy]
end

# Create isolated timeline
timeline "experiment_v2" {
    # Modify pipeline in this timeline
    pipeline features_v2:
        from customers
        derive new_feature = col_a * col_b
        features [new_feature, age]
        target outcome
    end
    
    experiment v2_exp:
        model random_forest
        using features_v2
        metrics [accuracy]
    end
}

# Merge best timeline back
merge "experiment_v2" into "main"

# Or restore checkpoint
undo "baseline"
```

## 📋 Command-Line Usage

```bash
# Run a script
fusionflow script.ff

# Print AST (for debugging)
fusionflow --print-ast script.ff

# Show runtime state after execution
fusionflow --print-state script.ff

# Debug mode
fusionflow --debug script.ff
```

## 📖 Documentation

**New to FusionFlow?** Start here:
- **[How to Use FusionFlow](HOW_TO_USE_FUSIONFLOW.md)** ← Complete 8-step guide for beginners
- **[Quick Reference](QUICK_REFERENCE.md)** ← One-page cheat sheet (bookmark this!)

**Technical Documentation:**
- [Architecture](ARCHITECTURE.md) - System design and components
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md) - Code walkthrough
- [Why FusionFlow is Unique](WHY_FUSIONFLOW_IS_UNIQUE.md) - Differentiation & positioning

**For Maintainers:**
- [Publish to VS Code Marketplace](PUBLISH_VS_CODE_EXTENSION.md)
- [Distribute Windows .exe](DISTRIBUTE_WINDOWS_EXE.md)
- [Patent Filing Summary](PATENT_FILING_SUMMARY.md)

## 🛠️ Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
black fusionflow/

# Type check
mypy fusionflow/
```

## 📐 Architecture

FusionFlow consists of:

1. **Lexer** (`lexer.py`) — Tokenizes source code
2. **Parser** (`parser.py`) — Builds Abstract Syntax Tree (AST)
3. **AST Nodes** (`ast_nodes.py`) — Structured representation
4. **Runtime** (`runtime.py`) — State management with temporal branching
5. **Interpreter** (`interpreter.py`) — Executes AST using Pandas/scikit-learn
6. **CLI** (`__main__.py`) — Command-line interface

### Future: UPEG Backend Planner

The Unified Polyglot Execution Graph (UPEG) will enable:
- Capability-aware backend selection (Pandas → Spark → GPU)
- Cross-backend marshalling with provenance preservation
- Runtime cost-based optimization
- Polyglot code execution (Python/Java/JVM)

## 🎯 Use Cases

- **Rapid ML prototyping** with clean, declarative syntax
- **Reproducible experiments** with checkpoint/timeline branching
- **Data pipeline development** with built-in lineage tracking
- **What-if analysis** through isolated timeline execution

## 📄 License

MIT License - see LICENSE file

## 🤝 Contributing

Contributions welcome! This is an experimental language designed for:
- Research in programming language design
- Temporal semantics in data pipelines
- Provenance-aware optimization
- Multi-backend execution planning

## 🔗 Related Work

- [dbt](https://www.getdbt.com/) — SQL-based data transformation
- [Kedro](https://kedro.org/) — Python data pipeline framework
- [Apache Beam](https://beam.apache.org/) — Unified batch/streaming model
- [Kubeflow Pipelines](https://www.kubeflow.org/) — ML workflow orchestration

---

**Status**: Alpha / Proof of Concept

Built with ❤️ for exploring novel programming language concepts in data engineering and ML.
