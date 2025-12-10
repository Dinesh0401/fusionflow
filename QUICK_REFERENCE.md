# 🚀 FusionFlow Quick Reference - Everything You Need to Know

---

## 📦 Installation & Getting Started

### For Python Developers
```bash
pip install fusionflow
fusionflow my_script.ff
```

### For Windows Users
- Download `fusionflow-cli.exe` from [GitHub Releases](https://github.com/yourusername/fusionflow/releases)
- Put it in your project folder
- Run: `fusionflow-cli.exe my_script.ff`

### For IDE Users
- Open VS Code Extensions
- Search "FusionFlow"
- Click Install
- Get syntax highlighting + snippets for `.ff` files

---

## 📝 Basic Syntax

### Load Data
```fusionflow
dataset customers from "customers.csv"
dataset events from "events.parquet" versioned true
```

### Define Pipeline (Data Prep + Feature Engineering)
```fusionflow
pipeline my_pipeline:
    from customers
    join events on customers.id == events.user_id
    where age > 18
    derive spend_per_day = amount / days
    features [spend_per_day, age, category]
    target purchased
    split 80% train, 20% test
end
```

### Train ML Model
```fusionflow
experiment my_exp:
    model random_forest           # random_forest, xgboost, logistic_regression, neural_network, etc.
    using my_pipeline
    metrics [accuracy, f1, precision, recall, auc]
end
```

### See Results
```fusionflow
print metrics of my_exp
```

### Full Example
```fusionflow
dataset customers from "customers.csv"

pipeline churn_model:
    from customers
    where active == 1
    derive spend_per_day = amount / days
    features [spend_per_day, age, tenure]
    target churned
end

experiment baseline:
    model random_forest
    using churn_model
    metrics [accuracy, f1]
end

print metrics of baseline
```

---

## ⭐ Unique Feature: Temporal Branching

### Save a Checkpoint
```fusionflow
checkpoint "baseline"

experiment baseline:
    model random_forest
    using features_v1
    metrics [accuracy]
end
```

### Try Alternative in Isolated Timeline
```fusionflow
timeline "experiment_v2" {
    pipeline features_v2:
        from customers
        derive interaction = spend_per_day * age
        features [spend_per_day, age, interaction]
        target churned
    end
    
    experiment v2:
        model xgboost
        using features_v2
        metrics [accuracy]
    end
}
```

### Merge Best Version Back
```fusionflow
merge "experiment_v2" into "main"
```

### Compare All Versions
```fusionflow
print metrics of baseline
print metrics of v2
```

---

## 🎯 Commands

### Run a Script
```bash
fusionflow script.ff
```

### View AST (Debugging)
```bash
fusionflow --print-ast script.ff
```

### Show Runtime State
```bash
fusionflow --print-state script.ff
```

### Debug Mode
```bash
fusionflow --debug script.ff
```

### Help
```bash
fusionflow --help
fusionflow --version
```

---

## 📊 Models Supported

- `random_forest` - Classification/Regression
- `logistic_regression` - Binary/Multiclass classification
- `xgboost` - High-performance gradient boosting
- `neural_network` - Deep learning
- `decision_tree` - Interpretable models
- `svm` - Support vector machines
- `gradient_boosting` - Ensemble method

---

## 📈 Metrics Available

**Classification:**
- `accuracy` - Overall correctness
- `f1` - Balanced precision-recall
- `precision` - True positives / predicted positive
- `recall` - True positives / actual positive
- `auc` - Area under ROC curve

**Regression:**
- `mse` - Mean squared error
- `rmse` - Root mean squared error
- `r2` - Coefficient of determination

---

## 🧠 What FusionFlow Does For You

| You Write | FusionFlow Does |
|-----------|-----------------|
| `.ff` script | ✅ Parses syntax |
| dataset/pipeline/experiment declarations | ✅ Loads data, applies transformations |
| model + metrics | ✅ Trains ML model, calculates metrics |
| checkpoint/timeline/merge | ✅ Manages what-if experiments |
| features [col1, col2] + target outcome | ✅ Auto-splits into train/test, handles feature engineering |

---

## 📂 File Structure

Create a project like this:

```
my_ml_project/
├── my_pipeline.ff           ← Your FusionFlow script
├── customers.csv            ← Your data
├── events.csv               ← More data (optional)
└── README.md                ← Documentation
```

Run:
```bash
fusionflow my_pipeline.ff
```

---

## 🔗 Common Workflows

### Workflow 1: Quick Prototype
```bash
fusionflow prototype.ff
# Results instantly in terminal
```

### Workflow 2: Compare Models
```fusionflow
experiment exp_rf:
    model random_forest
    using features
    metrics [accuracy, f1]
end

experiment exp_xgb:
    model xgboost
    using features
    metrics [accuracy, f1]
end

print metrics of exp_rf
print metrics of exp_xgb
```

### Workflow 3: Feature Engineering A/B Test
```fusionflow
checkpoint "baseline"

experiment baseline:
    model random_forest
    using simple_features
    metrics [accuracy]
end

timeline "advanced_features" {
    experiment advanced:
        model random_forest
        using engineered_features
        metrics [accuracy]
    end
}

merge "advanced_features" into "main"

print metrics of baseline
print metrics of advanced
```

### Workflow 4: Production Deployment
```fusionflow
# Train model
experiment prod_model:
    model random_forest
    using features
    metrics [accuracy, f1, precision, recall]
end

# When ready: extract model and deploy elsewhere
# print model of prod_model
```

---

## 🐛 Debug Tips

### Check Loaded Data
```bash
fusionflow --print-state my_script.ff
```

### Print intermediate steps
```fusionflow
pipeline debug_pipeline:
    from data
    where age > 18
    print          ← Shows data after each step
    
    derive new_col = amount * 2
    print          ← Shows updated data
    
    features [new_col, age]
    target outcome
end
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "File not found: data.csv" | CSV not in same folder | Put CSV in project folder |
| "Column 'xyz' not found" | Typo in column name | Check CSV headers |
| "Expected IDENT, got FEATURES" | Using keyword as column name | Rename column in CSV |
| Module import error | Dependencies missing | `pip install pandas scikit-learn` |

---

## 🎯 Publishing Your Work

### Publish to PyPI (Developers)
```bash
pip install fusionflow
# Available to all Python developers globally
```

### Publish VS Code Extension
1. Go to [VS Code Marketplace](https://marketplace.visualstudio.com/)
2. Create publisher account
3. Run: `vsce publish`
4. Users search "FusionFlow" and install

See: [PUBLISH_VS_CODE_EXTENSION.md](PUBLISH_VS_CODE_EXTENSION.md)

### Publish Windows .exe
1. Run PyInstaller: `pyinstaller --onefile fusionflow/__main__.py`
2. Create GitHub Release
3. Upload `dist/fusionflow-cli.exe`
4. Users download + run

See: [DISTRIBUTE_WINDOWS_EXE.md](DISTRIBUTE_WINDOWS_EXE.md)

---

## 🌟 Why FusionFlow is Unique

| Feature | FusionFlow | SQL | Python | Airflow |
|---------|-----------|-----|--------|---------|
| Temporal Branching | ✅ Built-in | ❌ | ❌ | ❌ External |
| Language DSL | ✅ `.ff` | ✅ `.sql` | ❌ `.py` | ❌ YAML |
| Adaptive Backends | ✅ Auto | ❌ Manual | ❌ Manual | ❌ Manual |
| What-If Experiments | ✅ Easy | ❌ | ❌ | ❌ Complex |
| Provenance Tracking | ✅ Built-in | ❌ | ❌ Manual | ⚠️ Partial |

**FusionFlow = SQL's elegance + Python's flexibility + Temporal semantics**

---

## 📚 Documentation

| Doc | Purpose |
|-----|---------|
| `README.md` | Quick start |
| `HOW_TO_USE_FUSIONFLOW.md` | Complete user guide |
| `ARCHITECTURE.md` | How FusionFlow works internally |
| `IMPLEMENTATION_SUMMARY.md` | Code walkthrough |
| `WHY_FUSIONFLOW_IS_UNIQUE.md` | Why it's not "just Python" |
| `PUBLISH_VS_CODE_EXTENSION.md` | Publish to VS Code Marketplace |
| `DISTRIBUTE_WINDOWS_EXE.md` | Create Windows executable |
| `PATENT_FILING_SUMMARY.md` | Patent documentation |

---

## 💡 Key Concepts

### Dataset
Collection of data you want to analyze
```fusionflow
dataset customers from "customers.csv"
```

### Pipeline
Sequence of transformations (filters, joins, features, target)
```fusionflow
pipeline my_pipeline:
    from customers
    where age > 18
    derive spend = amount / days
    features [spend, age]
    target outcome
end
```

### Experiment
Train an ML model on a pipeline
```fusionflow
experiment my_exp:
    model random_forest
    using my_pipeline
    metrics [accuracy]
end
```

### Checkpoint
Save current state as a reference point
```fusionflow
checkpoint "baseline"
```

### Timeline
Create isolated alternative (doesn't affect main)
```fusionflow
timeline "experiment_v2" { ... }
```

### Merge
Integrate timeline back into main
```fusionflow
merge "experiment_v2" into "main"
```

---

## 🚀 Next Steps

1. **Install:** `pip install fusionflow` or download `.exe`
2. **Try example:** Create `churn.ff` from template above
3. **Run:** `fusionflow churn.ff`
4. **Explore temporal branching:** Add checkpoint/timeline
5. **Deploy:** Use Python or Windows installer
6. **Share:** Publish to VS Code Marketplace or PyPI

---

## 🆘 Need Help?

- **GitHub Issues:** Report bugs
- **GitHub Discussions:** Ask questions
- **Documentation:** See markdown files in repo
- **Examples:** Check `examples/` folder

---

## 📊 Project Status

| Component | Status |
|-----------|--------|
| Language (Lexer, Parser, Runtime) | ✅ Complete |
| ML Training (sklearn) | ✅ Complete |
| Temporal Branching | ✅ Complete |
| VS Code Extension | ✅ Packaged |
| Testing (43/43 passing) | ✅ Complete |
| Documentation | ✅ Complete |
| Windows .exe | ✅ Ready |
| Patent Filing | ✅ Ready |

---

## 🎉 You're Ready!

Download FusionFlow, write your first `.ff` script, and start building temporal ML pipelines today.

**Happy pipelining!** 🎊

