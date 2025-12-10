"""FusionFlow CLI - Main entry point"""

import sys
import argparse
from fusionflow.lexer import Lexer
from fusionflow.parser import Parser
from fusionflow.interpreter import Interpreter
from fusionflow.runtime import Runtime

def main():
    parser = argparse.ArgumentParser(description='FusionFlow - Temporal ML Pipeline DSL')
    parser.add_argument('file', nargs='?', help='FusionFlow script file (.ff)')
    parser.add_argument('--version', action='store_true', help='Show version')
    parser.add_argument('--print-ast', action='store_true', help='Print AST')
    parser.add_argument('--print-state', action='store_true', help='Print runtime state')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    
    args = parser.parse_args()
    
    if args.version:
        print("FusionFlow v0.1.0")
        return 0
    
    if not args.file:
        parser.print_help()
        return 1
    
    try:
        with open(args.file, 'r') as f:
            source = f.read()
        
        # Lexical analysis
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        if args.debug:
            print("=== TOKENS ===")
            for token in tokens:
                print(token)
            print()
        
        # Parsing
        parser_obj = Parser(tokens)
        ast = parser_obj.parse()
        
        if args.print_ast:
            print("=== AST ===")
            print(ast)
            print()
        
        # Interpretation
        runtime = Runtime()
        interpreter = Interpreter(runtime)
        interpreter.execute(ast)
        
        if args.print_state:
            print("\n=== RUNTIME STATE ===")
            print(f"Datasets: {list(runtime.datasets.keys())}")
            print(f"Pipelines: {list(runtime.pipelines.keys())}")
            print(f"Experiments: {list(runtime.experiments.keys())}")
            print(f"Checkpoints: {list(runtime.checkpoints.keys())}")
            print(f"Current Timeline: {runtime.current_timeline}")
        
        return 0
    
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found", file=sys.stderr)
        return 1
    except SyntaxError as e:
        print(f"Syntax Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
