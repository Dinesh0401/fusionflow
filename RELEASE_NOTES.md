# FusionFlow v0.1.0 Release Notes

**Release Date:** December 10, 2025

## 🎉 First Official Release

FusionFlow v0.1.0 is a complete temporal ML pipeline DSL with first-class branching primitives.

## ✨ What's New

### Core Language Features
- **Complete DSL Implementation**: Lexer, parser, and interpreter for `.ff` files
- **Temporal Branching**: `checkpoint`, `timeline`, `merge`, and `undo` primitives
- **ML Pipeline Support**: Dataset loading, transformations, feature engineering, train/test splits
- **Built-in Models**: Random Forest and Logistic Regression with automatic training
- **Metrics**: accuracy, f1, precision, recall, AUC evaluation

### Language Syntax
```fusionflow
dataset customers from "data.csv"

pipeline churn_pipeline:
    from customers
    where active == 1
    derive spend_per_day = amount / days
    features [spend_per_day, age]
    target churned
    split 80% train, 20% test
end

experiment churn_exp:
    model random_forest
    using churn_pipeline
    metrics [accuracy, f1]
end

print metrics of churn_exp
```

### Installation Options

#### 1. Python Users (pip)
```bash
pip install fusionflow
```

Run scripts:
```bash
fusionflow script.ff
```

#### 2. Windows Users (.exe - No Python Required)
Download `fusionflow-cli-0.1.0-windows.exe` (210MB) from [GitHub Releases](https://github.com/Dinesh0401/fusionflow/releases/tag/v0.1.0)

Run from command line:
```cmd
fusionflow-cli-0.1.0-windows.exe script.ff
```

#### 3. VS Code Extension
Install from VS Code Marketplace or `.vsix` file:
- Syntax highlighting for `.ff` files
- Keyword recognition
- Auto-closing brackets

#### 4. From Source
```bash
git clone https://github.com/Dinesh0401/fusionflow.git
cd fusionflow
pip install -e .
```

## 📦 What's Included

### Core Components
- **Lexer** (134 lines): 70+ token types, keyword handling
- **Parser** (393 lines): Full AST generation
- **Interpreter** (309 lines): Pandas + scikit-learn execution
- **Runtime** (104 lines): Copy-on-write temporal branching
- **CLI** (`fusionflow` command): `--version`, `--print-ast`, `--debug` flags

### Testing
- **43 tests passing** (100% success rate)
- Test suites: lexer, parser, end-to-end, comprehensive
- Coverage: keyword handling, Windows paths, complex pipelines, temporal branching

### Documentation
- [How to Use FusionFlow](https://github.com/Dinesh0401/fusionflow/blob/main/HOW_TO_USE_FUSIONFLOW.md) - Complete beginner guide
- [Quick Reference](https://github.com/Dinesh0401/fusionflow/blob/main/QUICK_REFERENCE.md) - One-page cheat sheet
- [Architecture](https://github.com/Dinesh0401/fusionflow/blob/main/ARCHITECTURE.md) - System design
- [Publish VS Code Extension](https://github.com/Dinesh0401/fusionflow/blob/main/PUBLISH_VS_CODE_EXTENSION.md)
- [Distribute Windows .exe](https://github.com/Dinesh0401/fusionflow/blob/main/DISTRIBUTE_WINDOWS_EXE.md)

### Branding
- Professional FF logo with blue (#4682E6) and orange (#FF8C32) colors
- Multi-resolution assets (16px-512px)
- Windows ICO file embedded in .exe

## 🎯 Example Use Cases

1. **Rapid ML Prototyping**: Clean, declarative syntax for quick experiments
2. **Reproducible Experiments**: Checkpoint/timeline branching for version control
3. **What-If Analysis**: Test different feature sets in isolated timelines
4. **Data Pipeline Development**: Built-in lineage tracking

## 🔧 Technical Details

- **Python**: 3.8+ (3.10+ recommended)
- **Dependencies**: pandas, scikit-learn, numpy
- **File Extension**: `.ff`
- **Execution**: Python interpreter or standalone .exe

## 📊 Performance

- Dataset loading: CSV, Parquet support
- Execution: Native Pandas operations
- Model training: scikit-learn backend
- .exe size: 210MB (includes all dependencies)

## 🐛 Known Issues

- UPEG (Unified Polyglot Execution Graph) is foundational but not fully implemented
- Spark backend adapter is placeholder only
- No GPU execution support yet
- Join operations are basic (inner join only)

## 🚀 Coming in v0.2.0

- Full UPEG backend planner implementation
- Spark execution backend
- Advanced join types (left, right, outer)
- GPU acceleration support
- Column-level lineage tracking
- Interactive REPL mode
- Jupyter notebook integration
- More ML models (XGBoost, LightGBM, neural networks)

## 📄 License

MIT License - See [LICENSE](https://github.com/Dinesh0401/fusionflow/blob/main/LICENSE) file

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](https://github.com/Dinesh0401/fusionflow/blob/main/CONTRIBUTING.md)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Dinesh0401/fusionflow/issues)
- **Documentation**: [GitHub Wiki](https://github.com/Dinesh0401/fusionflow)
- **Repository**: https://github.com/Dinesh0401/fusionflow

---

**Full Changelog**: https://github.com/Dinesh0401/fusionflow/commits/v0.1.0
