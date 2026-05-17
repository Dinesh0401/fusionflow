"""FusionFlow CLI - Main entry point"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

from fusionflow import __version__
from fusionflow.executor import (
    NoopBackend,
    PandasBackend,
    RunContext,
    RunStatus,
    load_plan,
)
from fusionflow.interpreter import Interpreter
from fusionflow.ir_export import build_temporal_ir
from fusionflow.lexer import Lexer
from fusionflow.parser import Parser
from fusionflow.runtime import Runtime


def _build_runtime(source: str) -> Tuple[Runtime, List[Any], Any]:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser_obj = Parser(tokens)
    ast = parser_obj.parse()
    runtime = Runtime()
    interpreter = Interpreter(runtime)
    interpreter.execute(ast)
    return runtime, tokens, ast


def handle_run(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="FusionFlow - Temporal ML Pipeline DSL")
    parser.add_argument("file", nargs="?", help="FusionFlow script file (.ff)")
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--print-ast", action="store_true", help="Print AST")
    parser.add_argument("--print-state", action="store_true", help="Print runtime state")
    parser.add_argument("--debug", action="store_true", help="Debug mode")

    args = parser.parse_args(list(argv))

    if args.version:
        print(f"FusionFlow v{__version__}")
        return 0

    if not args.file:
        parser.print_help()
        return 1

    try:
        source = Path(args.file).read_text(encoding="utf-8")
        runtime, tokens, ast = _build_runtime(source)

        if args.debug:
            print("=== TOKENS ===")
            for token in tokens:
                print(token)
            print()

        if args.print_ast:
            print("=== AST ===")
            print(ast)
            print()

        if args.print_state:
            print("\n=== RUNTIME STATE ===")
            dataset_keys = sorted(
                f"{name}:{version}" for name, version in runtime.datasets.keys()
            )
            print(f"Datasets: {dataset_keys}")
            print(f"Pipelines: {sorted(runtime.pipelines.keys())}")
            print(f"Models: {sorted(runtime.models.keys())}")
            print(f"Timelines: {sorted(runtime.timelines.keys())}")
            main_timeline = runtime.timelines.get("main")
            if main_timeline:
                print(f"Main experiments: {sorted(main_timeline.experiments.keys())}")
            print(f"Merges: {len(runtime.merges)}")

        return 0

    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found", file=sys.stderr)
        return 1
    except SyntaxError as exc:
        print(f"Syntax Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if args.debug:
            import traceback

            traceback.print_exc()
        return 1


def handle_compile(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Compile FusionFlow spec to Temporal IR JSON")
    parser.add_argument("file", help="FusionFlow spec file (.ff)")
    parser.add_argument("--out", dest="out_path", help="Write JSON output to file")
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON without indentation",
    )

    args = parser.parse_args(list(argv))

    try:
        source = Path(args.file).read_text(encoding="utf-8")
        runtime, _, _ = _build_runtime(source)
        ir_payload = build_temporal_ir(runtime)
        indent = None if args.compact else 2
        json_output = json.dumps(ir_payload, indent=indent)

        if args.out_path:
            Path(args.out_path).write_text(json_output + "\n", encoding="utf-8")
        else:
            print(json_output)

        return 0

    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found", file=sys.stderr)
        return 1
    except SyntaxError as exc:
        print(f"Syntax Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def handle_validate(argv: Sequence[str]) -> int:
    """`fusionflow validate path/to/spec.ff` -- syntactic + semantic check, no execution."""
    parser = argparse.ArgumentParser(
        description="Validate a FusionFlow specification (parses + interprets)."
    )
    parser.add_argument("file", help="FusionFlow spec file (.ff)")

    args = parser.parse_args(list(argv))

    try:
        source = Path(args.file).read_text(encoding="utf-8")
        _build_runtime(source)
        print(f"OK: {args.file} is a valid FusionFlow specification.")
        return 0
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found", file=sys.stderr)
        return 1
    except SyntaxError as exc:
        print(f"Syntax Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def handle_diff(argv) -> int:
    parser = argparse.ArgumentParser(description="Diff two FusionFlow specs at the IR level")
    parser.add_argument("file_a", help="First .ff file (the 'before')")
    parser.add_argument("file_b", help="Second .ff file (the 'after')")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable diff")
    args = parser.parse_args(list(argv))

    try:
        source_a = Path(args.file_a).read_text(encoding="utf-8")
        source_b = Path(args.file_b).read_text(encoding="utf-8")
        runtime_a, _, _ = _build_runtime(source_a)
        runtime_b, _, _ = _build_runtime(source_b)
        ir_a = build_temporal_ir(runtime_a)
        ir_b = build_temporal_ir(runtime_b)

        from fusionflow.diff import diff_ir, format_diff_human, format_diff_json
        diff = diff_ir(ir_a, ir_b)

        if args.json:
            print(format_diff_json(diff))
        else:
            print(format_diff_human(diff), end="")

        # Exit code: 0 = identical, 1 = different
        return 0 if diff.is_empty else 1

    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except SyntaxError as exc:
        print(f"Syntax Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


def handle_visualize(argv) -> int:
    parser = argparse.ArgumentParser(description="Visualize a FusionFlow spec as a graph")
    parser.add_argument("file", help="The .ff file to visualize")
    parser.add_argument(
        "--format",
        choices=["mermaid", "dot", "html"],
        default="mermaid",
        help="Output format (default: mermaid)",
    )
    parser.add_argument("--out", dest="out_path", help="Write output to a file instead of stdout")
    args = parser.parse_args(list(argv))

    try:
        source = Path(args.file).read_text(encoding="utf-8")
        runtime, _, _ = _build_runtime(source)
        ir = build_temporal_ir(runtime)

        from fusionflow.visualize import visualize_ir
        rendered = visualize_ir(ir, fmt=args.format)

        if args.out_path:
            Path(args.out_path).write_text(rendered, encoding="utf-8")
            print(f"Wrote {args.format} visualization to {args.out_path}")
        else:
            print(rendered, end="")
        return 0

    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except SyntaxError as exc:
        print(f"Syntax Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


def _discover_experiments(runtime: Runtime) -> List[Tuple[str, str]]:
    """Return list of (timeline_name, experiment_name) pairs in deterministic order.

    Walks the main timeline first, then sub-timelines (sorted by name).
    """
    discovered: List[Tuple[str, str]] = []
    main = runtime.timelines.get("main")
    if main is not None:
        for exp_name in main.experiments.keys():
            discovered.append(("main", exp_name))
    for tl_name in sorted(runtime.timelines.keys()):
        if tl_name == "main":
            continue
        timeline = runtime.timelines[tl_name]
        for exp_name in timeline.experiments.keys():
            discovered.append((tl_name, exp_name))
    return discovered


def handle_run_executor(argv: Sequence[str]) -> int:
    """`fusionflow run path/to/spec.ff` -- execute one experiment via a backend."""
    parser = argparse.ArgumentParser(
        description="Run a FusionFlow experiment through the executor."
    )
    parser.add_argument("file", help="FusionFlow spec file (.ff)")
    parser.add_argument(
        "--experiment",
        dest="experiment",
        default=None,
        help="Experiment name. Defaults to the first experiment found.",
    )
    parser.add_argument(
        "--backend",
        choices=["pandas", "noop"],
        default="pandas",
        help="Execution backend (default: pandas)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for the backend (default: 42)",
    )
    parser.add_argument(
        "--num-threads",
        type=int,
        default=1,
        help="Threads for numpy/sklearn (default: 1 for determinism)",
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        default=None,
        help="Write RunResult JSON to this file. If omitted, JSON goes to stdout.",
    )
    parser.add_argument(
        "--data-root",
        dest="data_root",
        default=None,
        help="Base directory for resolving DatasetSpec source paths "
        "(default: directory of the .ff file).",
    )
    parser.add_argument(
        "--mlflow",
        action="store_true",
        help="Log the run to MLflow (requires `pip install fusionflow[mlflow]`).",
    )

    args = parser.parse_args(list(argv))

    try:
        spec_path = Path(args.file)
        source = spec_path.read_text(encoding="utf-8")
        runtime, _, _ = _build_runtime(source)
        ir_payload = build_temporal_ir(runtime)
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found", file=sys.stderr)
        return 1
    except SyntaxError as exc:
        print(f"Syntax Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Pick the experiment to run.
    discovered = _discover_experiments(runtime)
    if not discovered:
        print("Error: no experiments found in spec.", file=sys.stderr)
        return 1

    if args.experiment is None:
        experiment_name = discovered[0][1]
    else:
        experiment_name = args.experiment
        available = [name for _, name in discovered]
        if experiment_name not in available:
            print(
                f"Error: experiment '{experiment_name}' not found. "
                f"Available: {sorted(available)}",
                file=sys.stderr,
            )
            return 2

    # Build the plan.
    try:
        plan = load_plan(ir_payload, experiment_name)
    except Exception as exc:
        print(f"Error: failed to load plan: {exc}", file=sys.stderr)
        return 1

    # Construct backend.
    if args.backend == "pandas":
        data_root = (
            Path(args.data_root) if args.data_root is not None else spec_path.parent
        )
        ctx = RunContext(seed=args.seed, num_threads=args.num_threads)
        backend = PandasBackend(data_root=data_root, context=ctx)
    else:
        backend = NoopBackend()

    # Execute.
    try:
        result = backend.execute(plan)
    except Exception as exc:
        print(f"Error: backend raised during execution: {exc}", file=sys.stderr)
        return 1

    # Optional MLflow logging (opt-in via --mlflow flag).
    if args.mlflow and result.status != RunStatus.FAILED:
        try:
            from fusionflow.integrations.mlflow_logger import (
                MLflowNotInstalledError,
                log_run_result,
            )

            run_id = log_run_result(
                plan=plan,
                result=result,
                extra_params={"seed": args.seed, "num_threads": args.num_threads},
            )
            if run_id:
                print(f"Logged to MLflow: run_id={run_id}", file=sys.stderr)
        except MLflowNotInstalledError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    # Emit JSON.
    json_output = result.to_json()
    if args.out_path:
        Path(args.out_path).write_text(json_output + "\n", encoding="utf-8")
    else:
        print(json_output)

    # Exit code reflects the run status.
    if result.status == RunStatus.FAILED:
        if result.detail:
            print(f"Run failed: {result.detail}", file=sys.stderr)
        return 1
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if argv and argv[0] == "compile":
        return handle_compile(argv[1:])

    if argv and argv[0] == "validate":
        return handle_validate(argv[1:])

    if argv and argv[0] == "run":
        return handle_run_executor(argv[1:])

    if argv and argv[0] == "diff":
        return handle_diff(argv[1:])

    if argv and argv[0] == "visualize":
        return handle_visualize(argv[1:])

    return handle_run(argv)


if __name__ == "__main__":
    sys.exit(main())
