# FusionFlow VS Code Extension

Syntax highlighting and language support for FusionFlow temporal ML pipelines.

## What's new in 0.2.0

- 13 snippets for every v0.4 language construct — type `dataset`, `pipeline`,
  `model`, `experiment`, `timeline`, `merge`, `derive`, `where`, `split`,
  `features`, `target`, `checkpoint`, or `select` and press **Tab**.
- TextMate grammar covers the new v0.4 keywords (`where`, `split`, `features`,
  `checkpoint`).

## Features

- Syntax highlighting for `.ff` files
- Keyword recognition for FusionFlow constructs
- Auto-closing brackets and quotes
- Comment support

## Installation

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "FusionFlow"
4. Click Install

## Usage

Create a file with `.ff` extension and start writing FusionFlow pipelines!

## Example

```fusionflow
dataset customers from "data.csv"

pipeline churn_pipeline:
    from customers
    where active == 1
    features [age, income]
    target churned
    split 80% train, 20% test
end

experiment exp1:
    model random_forest
    using churn_pipeline
    metrics [accuracy, f1]
end

print metrics of exp1
```

## Companion CLI

The extension provides editor support; for execution, install the CLI:

```bash
pip install fusionflow
fusionflow run my_spec.ff --backend pandas
```

See https://github.com/Dinesh0401/fusionflow for full docs.
