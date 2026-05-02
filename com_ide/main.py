#!/usr/bin/env python3
"""
COM IDE - Main Entry Point

This is the main entry point for the COM IDE runtime.
It orchestrates the full pipeline:
  E+ Source → Lexer → Parser → AST → Signal IR → Python → Execution

Architecture Layers:
  (A) E+ Layer - User-facing DSL
  (B) Parser Layer - Tokenizer + AST Builder
  (C) Signal IR Layer - Intermediate Representation
  (D) Harness/Execution Layer - Python backend
  (E) Logging System - Structured logs
  (F) LLM Integration - Log analysis and knowledge (observer only)
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable

# Import all modules
from lexer import tokenize, LexerError
from parser import parse, ParseError
from eno_ast import ASTNode, Program, Assignment, Variable, Literal, Input, Output, BinaryOp, IfStatement, Loop, FunctionDef, FunctionCall, Return, Break, Exit, PropertyAccess
from signal_generator import generate_signal
from executor import execute_signal, ExecutionResult
from logger import get_logger, ExecutionLogger
from llm_analyzer import get_analyzer, LLMAnalyzer


class COMIDE:
    """
    COM IDE Runtime - Main orchestrator class.
    
    This class manages the complete execution pipeline from E+ source
    to executed result with logging and LLM analysis.
    """
    
    def __init__(
        self,
        log_dir: str = "./logs",
        knowledge_base_path: str = "./knowledge_base",
        input_provider: Optional[Callable[[str], str]] = None
    ):
        self.logger = get_logger(log_dir)
        self.analyzer = get_analyzer(knowledge_base_path)
        self.input_provider = input_provider
        self.execution_history: List[Dict[str, Any]] = []
    
    def compile(
        self,
        source_code: str
    ) -> Dict[str, Any]:
        """
        Compile E+ source code through the full pipeline.
        
        Returns a compilation result with:
        - success: bool
        - ast: AST dictionary (if successful)
        - signal: Signal IR (if successful)
        - error: Error message (if failed)
        - error_type: Type of error ('LEXER', 'PARSER', 'OTHER')
        """
        result = {
            "success": False,
            "ast": None,
            "signal": None,
            "error": None,
            "error_type": None
        }
        
        try:
            # Step 1: Parse source code to AST
            ast_program = parse(source_code)
            result["ast"] = ast_program.to_dict()
            
            # Step 2: Generate Signal IR from AST
            signal_ir = generate_signal(ast_program)
            result["signal"] = signal_ir
            
            result["success"] = True
            
        except LexerError as e:
            result["error_type"] = "LEXER"
            result["error"] = str(e)
            
        except ParseError as e:
            result["error_type"] = "PARSER"
            result["error"] = str(e)
            
        except Exception as e:
            result["error_type"] = "OTHER"
            result["error"] = str(e)
        
        return result
    
    def execute(
        self,
        source_code: str,
        log_execution: bool = True
    ) -> Dict[str, Any]:
        """
        Execute E+ source code through the full pipeline.
        
        This method:
        1. Compiles source to Signal IR
        2. Executes the Signal IR
        3. Logs the execution
        4. Stores in history
        
        Returns execution result with output, errors, and trace.
        """
        # Step 1: Compile
        compile_result = self.compile(source_code)
        
        if not compile_result["success"]:
            error_result = {
                "success": False,
                "output": "",
                "error": compile_result["error"],
                "error_type": compile_result["error_type"],
                "trace": [],
                "compile_result": compile_result
            }
            
            if log_execution:
                self.logger.log_error(
                    error_type=compile_result["error_type"],
                    error_message=compile_result["error"],
                    context={"source_code": source_code},
                    source_code=source_code
                )
            
            return error_result
        
        # Step 2: Execute Signal IR
        exec_result = execute_signal(
            compile_result["signal"],
            input_provider=self.input_provider
        )
        
        # Build full result
        result = {
            "success": exec_result.success,
            "output": exec_result.output,
            "error": str(exec_result.error) if exec_result.error else None,
            "trace": exec_result.trace,
            "return_value": exec_result.return_value,
            "duration_ms": exec_result.to_dict().get("duration_ms"),
            "compile_result": compile_result
        }
        
        # Step 3: Log execution
        if log_execution:
            log_entry = self.logger.log_execution(
                source_code=source_code,
                ast_dict=compile_result["ast"],
                signal_ir=compile_result["signal"],
                result=exec_result.to_dict(),
                error=str(exec_result.error) if exec_result.error else None
            )
            result["log_entry"] = log_entry
        
        # Step 4: Store in history
        self.execution_history.append(result)
        
        return result
    
    def analyze_last_execution(self) -> Dict[str, Any]:
        """Analyze the last execution using LLM analyzer."""
        if not self.execution_history:
            return {"error": "No executions to analyze"}
        
        # Get logs from logger
        logs = self.logger.get_recent_logs(count=10)
        
        # Analyze with LLM
        analysis = self.analyzer.analyze_logs(logs)
        
        return analysis
    
    def suggest_fix_for_last_error(self) -> Dict[str, Any]:
        """Get LLM suggestion for the last error."""
        if not self.execution_history:
            return {"error": "No executions to analyze"}
        
        last_result = self.execution_history[-1]
        
        if last_result["success"]:
            return {"info": "Last execution was successful, no fix needed"}
        
        error_context = {
            "error": last_result.get("error"),
            "error_type": last_result.get("error_type"),
            "output": last_result.get("output")
        }
        
        suggestion = self.analyzer.suggest_fix(error_context)
        
        return suggestion
    
    def add_knowledge_entry(
        self,
        problem: str,
        cause: str,
        fix: str,
        prevention: str,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Add a new knowledge entry to the wiki."""
        return self.analyzer.build_wiki_entry(
            problem=problem,
            cause=cause,
            fix=fix,
            prevention=prevention,
            tags=tags
        )
    
    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search the knowledge base."""
        return self.analyzer.search_knowledge(query)
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get all execution history."""
        return self.execution_history
    
    def export_logs(self, output_path: str) -> str:
        """Export all logs to a file."""
        return self.logger.export_logs(output_path)


def run_file(file_path: str, args: argparse.Namespace):
    """Run an E+ script from a file."""
    path = Path(file_path)
    
    if not path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    source_code = path.read_text(encoding="utf-8")
    
    # Create IDE instance
    ide = COMIDE(
        log_dir=args.log_dir,
        knowledge_base_path=args.kb_dir
    )
    
    # Execute
    result = ide.execute(source_code)
    
    # Output results
    if result["success"]:
        if result["output"]:
            print("\n--- OUTPUT ---")
            print(result["output"])
    else:
        print("\n--- ERROR ---")
        print(f"Type: {result.get('error_type', 'UNKNOWN')}")
        print(f"Message: {result.get('error', 'Unknown error')}")
    
    # Show LLM analysis if requested
    if args.analyze:
        print("\n")
        analysis = ide.analyze_last_execution()
        print(ide.analyzer.get_analysis_summary([analysis]))
    
    # Show suggestion if there was an error
    if not result["success"] and args.suggest:
        print("\n--- SUGGESTED FIX ---")
        suggestion = ide.suggest_fix_for_last_error()
        print(f"Suggestion: {suggestion.get('suggestion', 'No suggestion available')}")
        print(f"Confidence: {suggestion.get('confidence', 0):.1%}")
        print(f"Requires Confirmation: {suggestion.get('requires_confirmation', True)}")


def run_repl(args: argparse.Namespace):
    """Run interactive REPL mode."""
    print("=" * 50)
    print("COM IDE - E+ Interactive REPL")
    print("=" * 50)
    print("Type your E+ code and press Enter.")
    print("Commands:")
    print("  :quit     - Exit REPL")
    print("  :analyze  - Analyze last execution")
    print("  :history  - Show execution history")
    print("  :help     - Show this help")
    print("=" * 50)
    
    ide = COMIDE(
        log_dir=args.log_dir,
        knowledge_base_path=args.kb_dir
    )
    
    while True:
        try:
            line = input("\nE+> ").strip()
            
            if line == ":quit":
                print("Goodbye!")
                break
            
            if line == ":help":
                print("Commands: :quit, :analyze, :history, :help")
                continue
            
            if line == ":analyze":
                analysis = ide.analyze_last_execution()
                print(ide.analyzer.get_analysis_summary(ide.logger.get_recent_logs()))
                continue
            
            if line == ":history":
                history = ide.get_execution_history()
                print(f"\nExecution History ({len(history)} executions):")
                for i, entry in enumerate(history[-5:], 1):
                    status = "✓" if entry.get("success") else "✗"
                    print(f"  {i}. {status} - {entry.get('duration_ms', 0):.2f}ms")
                continue
            
            if not line:
                continue
            
            # Execute the code
            result = ide.execute(line)
            
            if result["success"]:
                if result["output"]:
                    print(f"\n{result['output']}")
            else:
                print(f"\nError [{result.get('error_type', 'UNKNOWN')}]: {result.get('error', 'Unknown error')}")
                
                # Auto-suggest if enabled
                if args.auto_suggest:
                    suggestion = ide.suggest_fix_for_last_error()
                    print(f"\n💡 Suggestion: {suggestion.get('suggestion', 'No suggestion available')}")
        
        except KeyboardInterrupt:
            print("\nInterrupted. Type :quit to exit.")
        except EOFError:
            break


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="COM IDE - E+ Language Runtime",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s script.eplus          # Run an E+ script
  %(prog)s script.eplus --analyze  # Run with LLM analysis
  %(prog)s --repl                  # Start interactive REPL
  %(prog)s --compile script.eplus  # Compile only (no execution)
        """
    )
    
    parser.add_argument(
        "file",
        nargs="?",
        help="E+ script file to execute"
    )
    
    parser.add_argument(
        "--repl",
        action="store_true",
        help="Start interactive REPL mode"
    )
    
    parser.add_argument(
        "--compile",
        action="store_true",
        help="Compile only, don't execute"
    )
    
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Run LLM analysis after execution"
    )
    
    parser.add_argument(
        "--suggest",
        action="store_true",
        help="Show LLM suggestions on errors"
    )
    
    parser.add_argument(
        "--auto-suggest",
        action="store_true",
        help="Auto-show suggestions on errors (REPL mode)"
    )
    
    parser.add_argument(
        "--log-dir",
        default="./logs",
        help="Directory for log files (default: ./logs)"
    )
    
    parser.add_argument(
        "--kb-dir",
        default="./knowledge_base",
        help="Directory for knowledge base (default: ./knowledge_base)"
    )
    
    parser.add_argument(
        "--export-logs",
        metavar="PATH",
        help="Export logs to specified path after execution"
    )
    
    args = parser.parse_args()
    
    # REPL mode
    if args.repl:
        run_repl(args)
        return
    
    # File execution
    if args.file:
        if args.compile:
            # Compile only
            path = Path(args.file)
            if not path.exists():
                print(f"Error: File not found: {args.file}")
                sys.exit(1)
            
            source_code = path.read_text(encoding="utf-8")
            ide = COMIDE(log_dir=args.log_dir, knowledge_base_path=args.kb_dir)
            result = ide.compile(source_code)
            
            if result["success"]:
                print("Compilation successful!")
                print("\n--- AST ---")
                print(json.dumps(result["ast"], indent=2))
                print("\n--- SIGNAL IR ---")
                print(json.dumps(result["signal"], indent=2))
            else:
                print(f"Compilation failed [{result['error_type']}]: {result['error']}")
                sys.exit(1)
        else:
            # Full execution
            run_file(args.file, args)
            
            # Export logs if requested
            if args.export_logs:
                ide = COMIDE(log_dir=args.log_dir, knowledge_base_path=args.kb_dir)
                output_path = ide.export_logs(args.export_logs)
                print(f"\nLogs exported to: {output_path}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
