# Changelog

All notable changes to the FusionFlow VS Code extension are documented here.

## [0.2.0] — 2026-05-11

### Added
- 13 code snippets for all v0.4 language constructs (dataset, pipeline, model,
  experiment, timeline, merge, derive, where, split, features, target,
  checkpoint, select). Type the prefix and press Tab.
- "Snippets" category in marketplace metadata so users can discover them.
- Automated marketplace publishing via `.github/workflows/publish-vscode.yml`
  (triggered by `vscode-v*` git tags).

### Changed
- TextMate grammar already supported the v0.4 keywords (`where`, `split`,
  `features`, `checkpoint`) — no grammar changes needed.

## [0.1.0]

### Added
- Initial release: syntax highlighting for `.ff` files.
- Language configuration (auto-closing brackets, comments).
