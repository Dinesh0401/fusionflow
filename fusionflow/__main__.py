"""FusionFlow CLI - Main entry point"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

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
        print("FusionFlow v0.1.0")
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


def main(argv: Optional[Sequence[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if argv and argv[0] == "compile":
        return handle_compile(argv[1:])

    return handle_run(argv)


if __name__ == "__main__":
    sys.exit(main())
