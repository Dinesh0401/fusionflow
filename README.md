# FusionFlow

**A Temporal Specification Language (TSL) for Machine Learning Experimentation**

FusionFlow is a domain-specific language (DSL) for **describing, versioning, and reasoning about machine‑learning experiments over time**.
 
Unlike traditional ML tools that execute scripts linearly, FusionFlow treats experiments as **temporal specifications**: immutable, branchable, mergeable descriptions of *what* was tried, *when*, and *why*.

A `.ff` file is **not a script** and **not a config file**. It is a **temporal contract** for reproducible ML experimentation.

---

## Project status

[![CI](https://github.com/Dinesh0401/fusionflow/actions/workflows/ci.yml/badge.svg)](https://github.com/Dinesh0401/fusionflow/actions/workflows/ci.yml)

**Current**: `v0.5.0-dev0` — syntax is **frozen** for the v0.5 cycle (see [`SYNTAX_FROZEN.md`](SYNTAX_FROZEN.md)).

**Stabilization phase.** The grammar, IR shape, CLI, and backend Protocol are committed surfaces. New features are additive only.

See:
- [`ROADMAP.md`](ROADMAP.md) — what's in v0.5, what's deferred to v0.6/v1.0
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to contribute
- [`DESIGN_PRINCIPLES.md`](DESIGN_PRINCIPLES.md) — the 7 decisions that explain the codebase
- [`ARCHITECTURE_OVERVIEW.md`](ARCHITECTURE_OVERVIEW.md) — 5-minute orientation
- [`scripts/demo-script.md`](scripts/demo-script.md) — 90-second demo

---

## What's new in v0.4.0

**FusionFlow runs.** The TSL stops being a spec and starts being a tool.

```bash
pip install fusionflow
fusionflow run my_spec.ff --backend pandas --seed 42
```

- **Real Pandas execution backend** — your `.ff` file actually trains a model and produces metrics.
- **`fusionflow validate`** subcommand — check a spec without running it.
- **Cross-process determinism** — same seed + same fixture -> byte-identical `RunResult` JSON.
- **Opt-in MLflow autologger** (`pip install fusionflow[mlflow]`) — params, metrics, IR artifact.
- **Jupyter `%%fusionflow` magic** (`pip install fusionflow[jupyter]`) — author and run pipelines inline.
- **VS Code extension v0.2.0** with 13 snippets for every v0.4 construct.
- **CI/CD** — automated PyPI publishing on `v*` tags, Marketplace publishing on `vscode-v*` tags.

See [`docs/getting-started.md`](docs/getting-started.md), [`docs/cli.md`](docs/cli.md), [`docs/backends.md`](docs/backends.md), [`docs/ir-spec-v0.4.md`](docs/ir-spec-v0.4.md).

---

## ✨ Core Ideas 

* **Temporal Specification Language (TSL)**
  Declare experiments, timelines, and merges explicitly. Time is a first‑class language concept.

* **Deterministic Temporal IR**
  FusionFlow compiles `.ff` files into a canonical, backend‑agnostic Temporal IR (JSON). Execution is downstream and optional.

* **Provenance‑Aware Semantics**
  Pipelines are pure transformations. Lineage is explicit and mergeable.

* **Backend Independence**
  The same `.ff` specification can target Pandas, Spark, GPU, or future engines without rewriting the source.

---

## 🚀 Installation

### Python Users

```bash
pip install fusionflow
```

### Windows Users (.exe – No Python Required)

Download the standalone executable from **GitHub Releases**.

### From Source

```bash
cd fusionflow
pip install -e .
```

---

## 🧠 What Makes `.ff` Files Special?

A `.ff` file:

* Describes **what experiments exist** (not how to run them)
* Encodes **experiment lineage and branching**
* Requires **explicit justification for merges**
* Is **diff‑able, reviewable, and auditable**
* Compiles to a **stable Temporal IR contract**

Think of `.ff` as:

* Terraform for ML experiments
* Git for experimentation timelines
* SQL for experimental intent

---

## 📖 Quick Start

Create `example.ff`:

```fusionflow
dataset customers v1
    source "customers.csv"
end

pipeline churn_features
    from customers v1
    derive spend_per_day = amount / days
    select [spend_per_day, age, tenure]
    target churned
end

model rf_v1
    type random_forest
    params { trees: 200 }
end

experiment churn_baseline
    uses pipeline churn_features
    uses model rf_v1
    metrics [accuracy, f1]
end
```

Compile the specification:

```bash
fusionflow compile example.ff --out churn.tir.json
```

This produces a **Temporal IR** describing the experiment graph.

---

## 🕰️ Temporal Branching

```fusionflow
timeline v2 "Interaction features"
    experiment churn_interaction
        uses pipeline churn_features
        extend {
            derive age_spend = age * spend_per_day
        }
        uses model rf_v1
        metrics [accuracy, f1]
    end
end

merge v2 into main
    because "Improved f1 without accuracy loss"
    strategy prefer_metrics f1
end
```

Rules:

* Timelines never mutate history
* Merges are explicit and justified
* Lineage and types are validated

---

## 🛠️ CLI Usage

```bash
# Compile to Temporal IR
fusionflow compile spec.ff

# Validate specification
fusionflow validate spec.ff

# Debug AST (language developers)
fusionflow --print-ast spec.ff
```

FusionFlow **does not execute ML by default**. Execution engines consume the IR.

---

## 📐 Architecture

FusionFlow consists of:

1. **Lexer / Parser** – Produces a typed AST
2. **Temporal Registry** – Records datasets, pipelines, experiments, timelines
3. **Temporal IR Exporter** – Emits canonical JSON
4. **CLI** – Validation and compilation

Execution backends are intentionally decoupled.

--- 

## 📄 Documentation

* **LANGUAGE_SPEC_v1.md** – Frozen language semantics
* **TEMPORAL_IR_v1.md** – IR schema and guarantees
* **ARCHITECTURE.md** – System design
* **WHY_FUSIONFLOW_IS_UNIQUE.md** – Positioning and research framing

---

## 🎯 Use Cases

* Reproducible ML experimentation
* What‑if analysis via timelines
* Auditable experiment review
* Research on temporal semantics in ML systems

---

## 🧪 Status

**v0.3.0 – TSL Freeze**

* Language semantics frozen
* Temporal IR stable
* Execution intentionally deferred

FusionFlow is now suitable for:

* Research publication
* External review
* Backend experimentation

---

## 📄 License

MIT License

---

## 🤝 Contributing

FusionFlow welcomes contributions in:

* Language design
* Temporal semantics
* IR tooling
* Backend adapters

Please read the language spec before proposing changes.
