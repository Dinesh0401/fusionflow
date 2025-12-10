# FusionFlow VS Code Extension

Syntax highlighting and language support for FusionFlow temporal ML pipelines.

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
