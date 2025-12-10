# 🚀 How to Use FusionFlow - Complete Guide

**For developers discovering FusionFlow for the first time**

---

## 🧩 Step 1: Install FusionFlow

### Option A: Python Developers (pip)

```bash
pip install fusionflow
```

Then you get a command-line tool:

```bash
fusionflow my_script.ff
```

### Option B: Windows Users (.exe download)

1. Go to [GitHub Releases](https://github.com/yourusername/fusionflow/releases)
2. Download `fusionflow-cli.exe`
3. Put it in your project folder
4. Run it directly:

```bash
fusionflow-cli.exe my_script.ff
```

---

## 🧩 Step 2: Install VS Code Extension

### Get syntax highlighting and code snippets

1. Open **VS Code**
2. Go to **Extensions** tab (Ctrl+Shift+X)
3. Search for **"FusionFlow"**
4. Click **Install**

Now `.ff` files show:
- ✅ Syntax highlighting (colored keywords)
- ✅ Code snippets (auto-complete)
- ✅ Comment support
- ✅ Smart bracket matching

---

## 🧩 Step 3: Create Your First Pipeline

Create a file called `churn.ff`:

```fusionflow
# Load your data
dataset customers from "customers.csv"

# Define pipeline: prepare features for ML
pipeline churn_model:
    from customers
    where active == 1
    derive spend_per_day = amount / days
    features [spend_per_day, age, tenure]
    target churned
    split 80% train, 20% test
end

# Train an ML model
experiment baseline:
    model random_forest
    using churn_model
    metrics [accuracy, f1, precision, recall]
end

# Print results
print metrics of baseline
```

**What each part does:**

| Part | Purpose |
|------|---------|
| `dataset ...` | Load CSV/Parquet data |
| `pipeline ...` | Data prep: joins, filters, feature engineering |
| `features [...]` | Which columns to use for ML |
| `target ...` | What you're predicting |
| `split ...` | Train/test split percentage |
| `experiment ...` | Train ML model on pipeline |
| `metrics [...]` | Performance metrics to calculate |
| `print ...` | Display results |

---

## 🧩 Step 4: Run Your Pipeline

In terminal:

```bash
fusionflow churn.ff
```

Output:

```
[runtime] loaded dataset customers (1000 rows)
[runtime] registered pipeline churn_model
[runtime] split: 800 train, 200 test
[runtime] trained experiment baseline with random_forest

=== Metrics for baseline ===
accuracy:  0.8700
f1:        0.7800
precision: 0.8200
recall:    0.7500
```

That's it! Your ML pipeline ran end-to-end.

---

## 🧩 Step 5: Use Temporal Branching (Your Superpower)

Want to try different approaches without losing the original?

FusionFlow lets you create **timelines** (parallel experiments) and **merge** them back:

```fusionflow
dataset customers from "customers.csv"

# Baseline approach
pipeline features_v1:
    from customers
    where active == 1
    derive spend_per_day = amount / days
    features [spend_per_day, age, tenure]
    target churned
end

# Save this as our baseline
checkpoint "baseline_features"

experiment baseline:
    model random_forest
    using features_v1
    metrics [accuracy, f1]
end

# Try a different approach in an isolated timeline
timeline "experiment_v2" {
    pipeline features_v2:
        from customers
        where active == 1
        # New approach: add interaction term
        derive interaction = spend_per_day * age
        features [spend_per_day, age, interaction, tenure]
        target churned
    end

    experiment v2:
        model xgboost  # Different model too
        using features_v2
        metrics [accuracy, f1]
    end
}

# Merge the best version back to main
merge "experiment_v2" into "main"

# Compare both approaches
print metrics of baseline
print metrics of v2
```

Output:

```
=== Metrics for baseline ===
accuracy: 0.8700
f1:       0.7800

=== Metrics for v2 ===
accuracy: 0.8950
f1:       0.8100

Timeline "experiment_v2" merged into main
```

**What happened:**
1. You ran baseline on original features
2. Created isolated timeline for v2
3. Ran v2 with new features and different model
4. Merged v2 back (keeping both experiments available)
5. Compared them side-by-side

No code duplication. No manual state management. Built into the language.

---

## 🧩 Step 6: Available Models and Metrics

### Supported ML Models

```fusionflow
experiment my_exp:
    model random_forest          # Classification/Regression
    using my_pipeline
    metrics [accuracy]
end
```

**All Models:**
- `random_forest`
- `logistic_regression`
- `xgboost`
- `neural_network`
- `decision_tree`
- `svm`
- `gradient_boosting`

### Available Metrics

```fusionflow
experiment my_exp:
    model random_forest
    using my_pipeline
    metrics [accuracy, f1, precision, recall, auc, mse, rmse, r2]
end
```

**Classification Metrics:**
- `accuracy` - correct predictions / total
- `f1` - balanced precision-recall
- `precision` - true positives / predicted positive
- `recall` - true positives / actual positive
- `auc` - area under ROC curve

**Regression Metrics:**
- `mse` - mean squared error
- `rmse` - root mean squared error
- `r2` - coefficient of determination

---

## 🧩 Step 7: Advanced Features

### Multiple Joins

```fusionflow
dataset customers from "customers.csv"
dataset orders from "orders.csv"
dataset payments from "payments.csv"

pipeline enriched_features:
    from customers
    join orders on customers.id == orders.customer_id
    join payments on orders.id == payments.order_id
    where customers.active == 1
    derive total_spent = payments.amount
    derive avg_order_value = total_spent / orders.count
    features [avg_order_value, customers.age, orders.frequency]
    target customers.churned
end
```

### Filtering and Transformation

```fusionflow
pipeline advanced:
    from raw_data
    where amount > 100 and active == 1
    derive revenue_category = 
        case 
            when amount > 1000 then "high"
            when amount > 500 then "medium"
            else "low"
        end
    features [revenue_category, age, region]
    target purchased
end
```

### Multiple Checkpoints

```fusionflow
# Checkpoint 1: Initial features
checkpoint "v1_basic_features"
experiment v1:
    model random_forest
    using basic_features
    metrics [accuracy]
end

# Checkpoint 2: Enhanced features
checkpoint "v2_enhanced_features"
experiment v2:
    model xgboost
    using enhanced_features
    metrics [accuracy]
end

# Compare all versions
print metrics of v1
print metrics of v2
```

### Checkpoint Restore

```fusionflow
# Try something experimental
timeline "risky_experiment" {
    # ... risky changes ...
}

# If you didn't like it, restore
undo "v1_basic_features"
```

---

## 🧩 Step 8: Use as Python Library (Optional)

If you want to embed FusionFlow in Python code:

```python
from fusionflow import run_script, run_string

# Run a .ff script
runtime = run_script("churn.ff")

# Access results programmatically
baseline_metrics = runtime["experiments"]["baseline"]["metrics"]
print(f"Accuracy: {baseline_metrics['accuracy']}")

# Or run from string
code = """
dataset customers from "customers.csv"
pipeline churn_model: ...
experiment baseline: ...
"""
runtime = run_string(code)
```

---

## 📋 Common Workflows

### Workflow 1: Quick Prototype

```bash
# 1. Create script
cat > prototype.ff << 'EOF'
dataset data from "data.csv"
pipeline prep:
    from data
    features [col1, col2, col3]
    target outcome
end
experiment exp:
    model random_forest
    using prep
    metrics [accuracy]
end
print metrics of exp
EOF

# 2. Run it
fusionflow prototype.ff
```

### Workflow 2: Compare Multiple Models

```fusionflow
dataset data from "data.csv"

pipeline features:
    from data
    features [age, income, credit_score]
    target approved
end

experiment rf:
    model random_forest
    using features
    metrics [accuracy, f1, auc]
end

experiment xgb:
    model xgboost
    using features
    metrics [accuracy, f1, auc]
end

experiment lr:
    model logistic_regression
    using features
    metrics [accuracy, f1, auc]
end

print metrics of rf
print metrics of xgb
print metrics of lr
```

### Workflow 3: Feature Engineering A/B Test

```fusionflow
dataset raw from "data.csv"

# Version A: Simple features
pipeline features_a:
    from raw
    features [age, income]
    target approved
end

# Version B: Engineered features
timeline "features_b_experiment" {
    pipeline features_b:
        from raw
        derive income_to_age = income / age
        derive income_category = 
            case when income > 100000 then "high" else "low" end
        features [age, income, income_to_age, income_category]
        target approved
    end
    
    experiment b:
        model random_forest
        using features_b
        metrics [accuracy]
    end
}

merge "features_b_experiment" into "main"

experiment a:
    model random_forest
    using features_a
    metrics [accuracy]
end

print metrics of a
print metrics of b
```

---

## 🐛 Debugging & Tips

### Print intermediate states

```fusionflow
dataset data from "data.csv"

pipeline prep:
    from data
    where active == 1
    print  # Print data after filter
    
    derive new_col = amount * 2
    print  # Print data after derivation
    
    features [new_col, age]
    target outcome
end
```

### Check what datasets are loaded

```bash
fusionflow --print-state my_script.ff
```

### Show AST for debugging

```bash
fusionflow --print-ast my_script.ff
```

---

## 📦 What You Need on Your Computer

### Minimum

- **Windows/Mac/Linux**
- **fusionflow** (installed via `pip` or `.exe`)
- **Your data** (CSV or Parquet files)
- **A text editor** (VS Code recommended)

### Optional

- **Python 3.8+** (if using `pip install`)
- **VS Code** (for syntax highlighting)

### Automatically included

- Pandas (data manipulation)
- scikit-learn (ML models)
- PyArrow (data format support)

---

## 🎯 Your First 5 Minutes

1. **Install:** `pip install fusionflow` or download `.exe`
2. **Install VS Code extension:** Search "FusionFlow" in Extensions
3. **Create file:** `my_pipeline.ff` with FusionFlow code
4. **Run:** `fusionflow my_pipeline.ff`
5. **See results:** Metrics printed in terminal

That's it. You're using FusionFlow.

---

## 🆘 Troubleshooting

### Error: "File not found: customers.csv"
- Put your CSV in the same folder as your `.ff` script
- Or use absolute path: `from "/full/path/to/customers.csv"`

### Error: "Column 'xyz' not found"
- Check CSV headers match your column names
- Use `derive` to create new columns
- Check `where` filters match column names

### Error: "Expected IDENT, got FEATURES"
- You're using a reserved keyword as a column name
- Rename the column in your CSV or in the `derive` step

### .exe doesn't work on Mac/Linux
- Use `pip install fusionflow` instead
- `.exe` is Windows-only; other platforms use the Python package

---

## 📚 Next Steps

1. **Read the examples:** Check `examples/` folder for full working scripts
2. **Join the community:** GitHub Discussions for questions
3. **Try temporal branching:** Create a `timeline` in your next script
4. **Advanced:** Read `ARCHITECTURE.md` to understand how FusionFlow works

---

## 🤝 Questions?

- **GitHub Issues:** Report bugs or ask questions
- **GitHub Discussions:** Community help
- **Documentation:** See `README.md` and `ARCHITECTURE.md`

---

**Happy pipelining! 🎉**
