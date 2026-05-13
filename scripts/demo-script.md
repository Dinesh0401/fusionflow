# FusionFlow 60–90 Second Demo Script

Three terminal panes, recorded with `asciinema`. Goal: show what FusionFlow uniquely enables in 90 seconds or less.

## Setup (off-camera, before recording)

```bash
pip install fusionflow
cd examples/
```

## Recording

### Scene 1 — "Specs are code" (15 sec)

```bash
# Show the .ff file
$ cat churn_prediction.ff
```

(Camera holds on the 25-line file for 5 seconds — viewers register that it's declarative, no Python.)

### Scene 2 — "It runs" (20 sec)

```bash
$ fusionflow run churn_prediction.ff --backend pandas --seed 42
# JSON RunResult prints with accuracy, f1
$ fusionflow run churn_prediction.ff --backend pandas --seed 42
# IDENTICAL output — viewer sees byte-determinism
```

(Caption: "Same seed = byte-identical metrics.")

### Scene 3 — "Branch and diff" (25 sec)

```bash
$ cp churn_prediction.ff churn_v2.ff
$ # quick edit: change `trees: 50` to `trees: 200`
$ fusionflow diff churn_prediction.ff churn_v2.ff
# Shows:
#   models:
#     ~ rf
#         params.trees
```

(Caption: "Semantic diff. Not git diff. The CHANGE, not the bytes.")

### Scene 4 — "Merge with justification" (20 sec)

```bash
$ cat timeline_merge_demo.ff | tail -10
# Highlight the `merge ... because ... strategy prefer_metrics rmse` block

$ fusionflow validate timeline_merge_demo.ff
# OK: timeline_merge_demo.ff is a valid FusionFlow specification.
```

(Caption: "Every merge requires a justification. Audit by design.")

### Scene 5 — Close (10 sec)

Text overlay:

```
FusionFlow
A temporal DSL for ML experiments
github.com/Dinesh0401/fusionflow
pip install fusionflow
```

## Production notes

- Use `asciinema rec demo.cast` then `agg demo.cast demo.gif` for a README-embeddable GIF.
- Terminal size: 100×30 minimum so JSON output isn't wrapped.
- Font size: at least 18pt for video viewers.
- Pace: don't speed up — viewers prefer to read along.

## Where to post

- GitHub README (embed as GIF near the top, after the v0.4 highlights section).
- LinkedIn (60-second clip).
- HackerNews / r/MachineLearning (link to the README's animated GIF).
- A blog post: "We froze the spec, then made it run, then made it diff."
