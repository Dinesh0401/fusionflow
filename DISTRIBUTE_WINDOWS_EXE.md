# 🪟 Distribute FusionFlow as Windows .exe

**Make FusionFlow downloadable for non-technical Windows users**

---

## 🎯 Overview

This guide turns your Python-based FusionFlow into a **single standalone `.exe` file** that Windows users can download and run without installing Python.

**Final result:**
- User downloads: `fusionflow-cli-0.1.0.exe`
- User runs: `fusionflow-cli-0.1.0.exe my_script.ff`
- No Python required ✅

---

## 📋 Prerequisites

- **Windows machine** (to build .exe)
- **Python 3.8+** installed
- **fusionflow package** set up with proper `__main__.py`
- **All dependencies listed** in `setup.py` or `pyproject.toml`

---

## 🔧 Step 1: Prepare Your Project

Your FusionFlow structure should look like:

```
fusionflow/
├── fusionflow/
│   ├── __init__.py
│   ├── __main__.py          ← IMPORTANT: CLI entry point
│   ├── lexer.py
│   ├── parser.py
│   ├── interpreter.py
│   └── ... (other modules)
├── setup.py  or  pyproject.toml
├── examples/
│   └── churn.ff
└── README.md
```

### 1a. Create/Update `fusionflow/__main__.py`

This is how your CLI gets triggered. Create if it doesn't exist:

```python
#!/usr/bin/env python3
"""
FusionFlow CLI Entry Point

Usage:
    fusionflow <script.ff>
    fusionflow --help
    fusionflow --version
"""

import sys
import os
from pathlib import Path

def main():
    """Main CLI entry point"""
    
    # Handle --help
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print("""
╔═══════════════════════════════════════════════════════════════╗
║                   FusionFlow v0.1.0                          ║
║  Polyglot, Provenance-Aware Pipeline Language                ║
╚═══════════════════════════════════════════════════════════════╝

USAGE:
    fusionflow <script.ff>

EXAMPLES:
    fusionflow my_pipeline.ff
    fusionflow --help
    fusionflow --version

DOCUMENTATION:
    https://github.com/yourusername/fusionflow

        """)
        sys.exit(0)
    
    # Handle --version
    if sys.argv[1] in ("--version", "-v"):
        print("FusionFlow v0.1.0")
        sys.exit(0)
    
    # Main: Run FusionFlow script
    script_path = sys.argv[1]
    
    # Check if file exists
    if not Path(script_path).exists():
        print(f"ERROR: File not found: {script_path}")
        sys.exit(1)
    
    # Read and run script
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            source = f.read()
        
        # Import runtime components
        from .lexer import tokenize
        from .parser import parse
        from .interpreter import evaluate
        
        # Parse and execute
        tokens = tokenize(source)
        ast = parse(tokens)
        evaluate(ast)
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 1b. Update `setup.py` or `pyproject.toml`

Make sure all dependencies are listed:

**setup.py:**
```python
from setuptools import setup, find_packages

setup(
    name="fusionflow",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.3.0",
        "scikit-learn>=1.0.0",
        "pyarrow>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "fusionflow=fusionflow.__main__:main",
        ],
    },
    python_requires=">=3.8",
)
```

**pyproject.toml:**
```toml
[project]
name = "fusionflow"
version = "0.1.0"
dependencies = [
    "pandas>=1.3.0",
    "scikit-learn>=1.0.0",
    "pyarrow>=8.0.0",
]

[project.scripts]
fusionflow = "fusionflow.__main__:main"
```

---

## 🔨 Step 2: Create a Clean Python Environment

This prevents build issues from system packages:

```bash
# Create virtual environment
python -m venv venv_build

# Activate it
venv_build\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install pandas scikit-learn pyarrow

# Install your package locally
pip install -e .
```

### Verify it works:

```bash
python -m fusionflow examples/churn.ff
```

Should run successfully and output metrics.

---

## 📦 Step 3: Install PyInstaller

PyInstaller converts Python → Windows .exe

```bash
pip install pyinstaller
```

Verify:
```bash
pyinstaller --version
```

---

## 🛠️ Step 4: Build the .exe

From your project root (where `fusionflow/` folder is):

```bash
pyinstaller --onefile --name fusionflow-cli --console fusionflow/__main__.py
```

**Flag explanation:**
- `--onefile` → Creates single .exe (not folder with 100 files)
- `--name fusionflow-cli` → Output filename: `fusionflow-cli.exe`
- `--console` → Shows console window (needed for output)
- `fusionflow/__main__.py` → Entry point script

**Process takes ~1-3 minutes**. When done:

```
dist/
  fusionflow-cli.exe    ← YOUR FINAL FILE
build/
  (temporary build files)
fusionflow.spec
```

Your executable is: **`dist/fusionflow-cli.exe`**

---

## ✅ Step 5: Test the .exe Locally

### 5a. Test in same folder

```bash
# Copy example data nearby
copy examples\churn.ff .
copy examples\customers.csv .

# Run the exe
dist\fusionflow-cli.exe churn.ff
```

Should output:
```
[runtime] loaded dataset customers (1000 rows)
[runtime] registered pipeline churn_model
[runtime] trained experiment baseline
=== Metrics for baseline ===
accuracy: 0.87
f1: 0.78
```

### 5b. Test from different folder

```bash
# Create a test directory
mkdir test_ff
cd test_ff

# Copy exe and files
copy ..\dist\fusionflow-cli.exe .
copy ..\examples\churn.ff .
copy ..\examples\customers.csv .

# Run from here
fusionflow-cli.exe churn.ff
```

Should work identically.

### 5c. Test --help

```bash
fusionflow-cli.exe --help
fusionflow-cli.exe --version
```

Both should show helpful output.

---

## 📤 Step 6: Distribute on GitHub Releases

GitHub Releases is the easiest way to share `.exe` files.

### 6a. Prepare the Release

```bash
# Copy exe to a clean folder with version
mkdir fusionflow-release
cd fusionflow-release
copy ..\dist\fusionflow-cli.exe .
copy ..\README.md .
copy ..\examples .

# Optional: Zip it
# (Right-click in Windows Explorer → Send to Compressed folder)
# Or from PowerShell:
Compress-Archive -Path fusionflow-cli.exe, README.md -DestinationPath fusionflow-0.1.0-win64.zip
```

### 6b. Create GitHub Release

1. Go to your GitHub repo
2. Click **Releases** (right side)
3. Click **"Draft a new release"**
4. Fill in:
   - **Tag version:** `v0.1.0`
   - **Release title:** `FusionFlow v0.1.0 - Windows Release`
   - **Description:**

```markdown
# FusionFlow v0.1.0 - Windows Release

The first official Windows .exe release!

## 🎉 What's New
- ✅ Standalone Windows executable
- ✅ No Python installation required
- ✅ Full temporal branching support
- ✅ 100% test pass rate

## 📥 Download

- **fusionflow-cli-0.1.0.exe** - Standalone executable
- **fusionflow-0.1.0-win64.zip** - Zip archive

## 🚀 Quick Start

1. Download `fusionflow-cli-0.1.0.exe`
2. Put it in your project folder
3. Create a `.ff` script (see examples below)
4. Run: `fusionflow-cli-0.1.0.exe my_script.ff`

## 📝 Example Script

Create `churn.ff`:

```fusionflow
dataset customers from "customers.csv"

pipeline churn_model:
    from customers
    where active == 1
    derive spend_per_day = amount / days
    features [spend_per_day, age]
    target churned
end

experiment baseline:
    model random_forest
    using churn_model
    metrics [accuracy, f1]
end

print metrics of baseline
```

Then run:

```bash
fusionflow-cli-0.1.0.exe churn.ff
```

## 📚 Documentation

See the full guide: [How to Use FusionFlow](https://github.com/yourusername/fusionflow/blob/main/HOW_TO_USE_FUSIONFLOW.md)

```

5. **Attach files:**
   - Click **"Attach binaries"** or drag & drop
   - Upload `fusionflow-cli-0.1.0.exe`
   - Upload `fusionflow-0.1.0-win64.zip` (optional)

6. Click **Publish release**

---

## 🔗 Step 7: Add Download Link to README

Update your main `README.md`:

```markdown
## 🚀 Installation

### Windows Users (.exe - No Python needed)

Go to [Releases](https://github.com/yourusername/fusionflow/releases) and download the latest `.exe`:

```bash
fusionflow-cli-0.1.0.exe your_script.ff
```

### Python Users (pip)

```bash
pip install fusionflow
fusionflow your_script.ff
```
```

---

## 🎯 Users' Experience

From a Windows user's perspective:

1. **Visit your GitHub**
2. **Click Releases**
3. **Download `fusionflow-cli-0.1.0.exe`**
4. **Put their `.ff` script and CSV in same folder**
5. **Double-click `fusionflow-cli-0.1.0.exe churn.ff` in PowerShell**
6. **See results**

No Python. No terminal knowledge. Just download → run.

---

## 📊 Build Multiple Versions

Later, create versions for different architectures:

```bash
# 64-bit (most common)
pyinstaller --onefile --name fusionflow-cli-win64 fusionflow/__main__.py

# 32-bit (older systems)
# (requires 32-bit Python installation)
pyinstaller --onefile --name fusionflow-cli-win32 fusionflow/__main__.py
```

Release both and let users choose.

---

## 🔄 Update Process

When you release v0.2.0:

1. Update version in `setup.py`:
   ```python
   version="0.2.0"
   ```

2. Rebuild exe:
   ```bash
   pyinstaller --onefile --name fusionflow-cli-v0.2.0 fusionflow/__main__.py
   ```

3. Create new GitHub Release with updated exe

4. Users download new version

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'pandas'"

**Solution:**
- Activate virtual environment: `venv_build\Scripts\activate`
- Install dependencies: `pip install pandas scikit-learn pyarrow`
- Rebuild: `pyinstaller --onefile --name fusionflow-cli --console fusionflow/__main__.py`

### Error: ".exe won't run"

**Solution:**
- Make sure `__main__.py` has proper entry point
- Test in virtual environment first: `python -m fusionflow examples/churn.ff`
- Check file paths are absolute or relative to exe location

### Error: "Cannot find CSV file"

**Solution:**
- User needs to put CSV in same folder as `.ff` script
- Or use absolute path in `.ff` script: `from "C:/full/path/data.csv"`
- Document this clearly in README

### Exe is too large (100+ MB)

**Solution:**
- This is normal (includes Python + all libraries)
- Can use `--onedir` instead to reduce size, but less portable
- Or use UPX to compress: `pyinstaller --onefile --upx-dir=upx fusionflow/__main__.py`

---

## ✨ Professional Polish (Optional)

### Add an Icon

Create or download a 256x256 icon (`icon.ico`), then:

```bash
pyinstaller --onefile --name fusionflow-cli --console --icon icon.ico fusionflow/__main__.py
```

### Add Windows File Associations

Later, create an installer (InnoSetup, NSIS) that:
- Registers `.ff` files with FusionFlow
- Adds to Start menu
- Creates uninstaller

But for v0.1.0, just the `.exe` is fine.

---

## 🎉 You Did It!

Your FusionFlow is now downloadable for any Windows user.

They can get started in **2 minutes** without knowing anything about Python or command lines.

---

## 📚 References

- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [GitHub Releases Help](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
- [Python Packaging Guide](https://packaging.python.org/)

