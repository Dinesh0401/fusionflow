# 📦 Publish FusionFlow to VS Code Marketplace

**Get your extension into the hands of developers everywhere**

---

## ✅ Prerequisites

Before you start, make sure you have:

- [ ] VS Code extension folder: `vscode-fusionflow/`
- [ ] Valid `package.json` with all required fields
- [ ] Syntax files: `syntaxes/fusionflow.tmLanguage.json`
- [ ] `Node.js` installed: `node -v` (should be v14+)
- [ ] `npm` installed: `npm -v`
- [ ] **Microsoft account** (free, takes 2 min to create)

---

## 🔧 Step 1: Install the VS Code Publishing Tool

```bash
npm install -g @vscode/vsce
```

Verify it works:

```bash
vsce -V
```

Should print version like `2.20.0` or similar.

---

## 🎫 Step 2: Create a Publisher (One-time setup)

Your "publisher" is like your brand name in the VS Code Marketplace.

### 2a. Go to Azure DevOps

Visit: **https://dev.azure.com/**

Sign in with your Microsoft account (or create one free).

### 2b. Create a Publisher

1. Look for **"Publish extensions"** or go to: https://marketplace.visualstudio.com/manage
2. Click **"Create publisher"**
3. Choose a name (e.g., `fusionflow-labs`, `your-name`, etc.)
   - Must be lowercase, no spaces
   - This will be your permanent publisher ID
4. Fill in publisher details
5. Click **Create**

**Example:**
```
Publisher name: fusionflow-labs
```

---

## 🔑 Step 3: Create a Personal Access Token (PAT)

This is your security key to publish from the command line.

### 3a. Generate the token

1. Go to: https://dev.azure.com/_usersettings/tokens
2. Click **"New Token"**
3. Fill in:
   - **Name:** `vsce-publish` (or anything you like)
   - **Organization:** All accessible organizations
   - **Expiration:** 90 days or longer
   - **Scopes:** Check **"Marketplace"** → **"Manage"**
4. Click **"Create"**
5. **Copy the token** (you'll only see it once!)

Save it somewhere safe (or keep the tab open).

---

## 📝 Step 4: Set Up Your Extension package.json

Edit `vscode-fusionflow/package.json` and make sure it looks like this:

```json
{
  "name": "fusionflow",
  "displayName": "FusionFlow Language Support",
  "description": "Syntax highlighting and snippets for FusionFlow (.ff) language",
  "version": "0.1.0",
  "publisher": "fusionflow-labs",
  "engines": {
    "vscode": "^1.80.0"
  },
  "categories": [
    "Programming Languages"
  ],
  "keywords": [
    "fusionflow",
    "ff",
    "dsl",
    "data-pipeline",
    "ml",
    "machine-learning",
    "temporal-branching"
  ],
  "icon": "icon.png",
  "repository": {
    "type": "git",
    "url": "https://github.com/yourusername/fusionflow"
  },
  "contributes": {
    "languages": [
      {
        "id": "fusionflow",
        "aliases": [
          "FusionFlow",
          "fusionflow"
        ],
        "extensions": [
          ".ff"
        ],
        "configuration": "./language-configuration.json"
      }
    ],
    "grammars": [
      {
        "language": "fusionflow",
        "scopeName": "source.fusionflow",
        "path": "./syntaxes/fusionflow.tmLanguage.json"
      }
    ],
    "snippets": [
      {
        "language": "fusionflow",
        "path": "./snippets/fusionflow.json"
      }
    ]
  }
}
```

**Key fields:**
- `publisher`: Must match your publisher ID from Step 2
- `version`: Semantic versioning (0.1.0 = early)
- `name`: lowercase, no spaces
- `displayName`: Pretty name users see
- `icons`: Nice to have (PNG file in root)

---

## 🔐 Step 5: Log In with vsce

```bash
vsce login fusionflow-labs
```

Replace `fusionflow-labs` with your publisher ID.

It will ask:

```
Provider (enter for the default ''):
```

Press Enter (use default).

Then:

```
Personal Access Token for publisher: [paste your token here]
```

Paste the token from Step 3.

If successful:

```
The PAT has been configured.
```

---

## 📦 Step 6: Package Your Extension

Inside your `vscode-fusionflow/` folder:

```bash
cd vscode-fusionflow
vsce package
```

This creates:

```
fusionflow-0.1.0.vsix
```

This is your installable extension file.

---

## 🚀 Step 7: Publish to Marketplace

Still in `vscode-fusionflow/`:

```bash
vsce publish
```

If you want to bump version explicitly:

```bash
vsce publish patch    # 0.1.0 → 0.1.1
vsce publish minor    # 0.1.0 → 0.2.0
vsce publish 0.2.0    # Explicit version
```

**What happens:**
1. `vsce` reads your `package.json`
2. Validates the extension
3. Uploads to VS Code Marketplace
4. In ~5 minutes, it appears in the Marketplace

---

## ✅ Step 8: Test as a Real User

### Option A: Fresh VS Code Install

On another machine:

1. Open **VS Code**
2. Go to **Extensions** (Ctrl+Shift+X)
3. Search: **"FusionFlow"** (or your exact `displayName`)
4. Install
5. Create a test file: `test.ff` with FusionFlow code
6. Verify syntax highlighting works ✅

### Option B: Local Testing (Before Publishing)

```bash
cd vscode-fusionflow
vsce package
code --install-extension fusionflow-0.1.0.vsix
```

This installs the `.vsix` locally for testing, without publishing.

---

## 📋 Pre-Publishing Checklist

Before you hit `vsce publish`, verify:

- [ ] `package.json` has correct `"publisher"` (matches your Marketplace publisher)
- [ ] `"name"` is lowercase, no spaces
- [ ] `"version"` follows semver (e.g., `0.1.0`)
- [ ] `"engines.vscode"` is reasonable (e.g., `^1.80.0`)
- [ ] `syntaxes/fusionflow.tmLanguage.json` exists and is valid JSON
- [ ] `language-configuration.json` exists
- [ ] `snippets/fusionflow.json` exists (if you have snippets)
- [ ] `README.md` exists (Marketplace displays this)
- [ ] Optional but nice: `icon.png` (128x128 square icon)
- [ ] `.gitignore` doesn't exclude your syntax/snippet files

---

## 🎯 After Publishing

### Link in your README

Update your main `README.md`:

```markdown
## 🎨 VS Code Extension

For syntax highlighting and code snippets, install the FusionFlow extension:

**Search:** "FusionFlow Language Support" in VS Code Extensions  
**Link:** [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=fusionflow-labs.fusionflow)

Or install directly:

```bash
code --install-extension fusionflow-labs.fusionflow
```
```

### Update future versions

When you release v0.2.0:

```bash
# Update version in package.json
# "version": "0.2.0"

cd vscode-fusionflow
vsce publish minor
```

---

## 🐛 Troubleshooting

### Error: "Publisher ID not recognized"

```
ERR Invalid publisher.
```

**Solution:**
- Make sure `"publisher"` in `package.json` matches exactly
- Make sure you created the publisher in Step 2
- Re-run `vsce login fusionflow-labs`

### Error: "Invalid Personal Access Token"

```
ERR Personal access token has expired.
```

**Solution:**
- Create a new token (Step 3)
- Run `vsce login fusionflow-labs` again
- Paste the new token

### Error: "Syntax file not found"

```
ERR File not found: syntaxes/fusionflow.tmLanguage.json
```

**Solution:**
- Make sure the file exists in your `vscode-fusionflow/` folder
- Check path in `package.json` is correct

### Extension published but not appearing in search

**Solution:**
- Wait 5-10 minutes (Marketplace indexes slowly)
- Search for exact `displayName` or publisher name
- Try refreshing VS Code: `Ctrl+Shift+P` → "Developer: Reload Window"

---

## 📊 Marketplace Page Tips

Your extension's Marketplace page shows:

1. **Icon** (from `icon.png`)
2. **Display Name** (from `displayName`)
3. **Description** (from `description`)
4. **Keywords** (from `keywords` array)
5. **README** (from `README.md` in your folder)

To improve discoverability:

- Use clear keywords: `fusionflow`, `dsl`, `data-pipeline`, `ml`, `temporal-branching`
- Write a helpful README with examples
- Make README show how to use the extension (syntax highlighting demo if possible)
- Keep description under 200 chars but descriptive

---

## 🎉 You Did It!

Your FusionFlow extension is now available to anyone who searches for it in VS Code.

They can install it with:

```
Ctrl+Shift+X → Search "FusionFlow" → Click Install
```

---

## 📚 References

- [VS Code Extension Publishing Guide](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)
- [vsce CLI Documentation](https://github.com/microsoft/vscode-vsce)
- [VS Code Marketplace](https://marketplace.visualstudio.com/)

