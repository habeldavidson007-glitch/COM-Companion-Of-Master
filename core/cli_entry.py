"""
Rich-based CLI entry point for COM IDE.
Provides a clean TUI with panels for Status, Input, Output, and Logs.
"""
import sys
import signal
from typing import Optional
from pathlib import Path
import logfire

from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.table import Table

from .pipeline import CompilerPipeline

logfire.configure(send_to_logfire=False)

console = Console()

class ComIdeCLI:
    """
    Rich-based CLI for COM IDE with real-time status updates.
    
    Design decisions:
    - Graceful shutdown on Ctrl+C
    - Real-time RAM/model status display
    - Clear separation of input/output/logs
    """
    
    def __init__(self):
        self.pipeline = CompilerPipeline()
        self.running = False
        self.current_ram_gb = 0.0
        self.current_model = "none"
        self.last_output = ""
        self.log_messages = []
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame) -> None:
        """Handle Ctrl+C gracefully."""
        logfire.info("Interrupt received, shutting down...")
        self.running = False
        console.print("\n[yellow]Shutting down COM IDE...[/yellow]")
        self._cleanup()
        sys.exit(0)

    def _cleanup(self) -> None:
        """Clean up resources before exit."""
        logfire.info("Cleaning up resources")
        # Stop any background monitoring
        from .ram_hardener import ram_hardener
        ram_hardener.stop_monitoring()

    def _get_ram_status(self) -> str:
        """Get current RAM usage string."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            used_gb = (mem.total - mem.available) / (1024 ** 3)
            self.current_ram_gb = used_gb
            total_gb = mem.total / (1024 ** 3)
            percent = mem.percent
            color = "green" if percent < 70 else "yellow" if percent < 90 else "red"
            return f"[{color}]RAM: {used_gb:.2f}GB / {total_gb:.2f}GB ({percent}%)[/{color}]"
        except ImportError:
            return "[gray]RAM: unavailable[/gray]"

    def _create_layout(self) -> Layout:
        """Create the main TUI layout."""
        layout = Layout()
        
        # Split into header, body, and footer
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=10)
        )
        
        # Split body into input and output
        layout["body"].split_row(
            Layout(name="input"),
            Layout(name="output")
        )
        
        return layout

    def _update_header(self, layout: Layout) -> None:
        """Update the header with status information."""
        status_table = Table(show_header=False, box=None, padding=(0, 1))
        status_table.add_column("Status", style="bold cyan")
        status_table.add_row("COM IDE v1.0")
        status_table.add_row(self._get_ram_status())
        status_table.add_row(f"Model: [{self.current_model}]")
        
        layout["header"].update(Panel(status_table, title="Status", border_style="blue"))

    def _update_input(self, layout: Layout, user_input: str = "") -> None:
        """Update the input panel."""
        input_text = Text(user_input or "Waiting for input...")
        layout["input"].update(Panel(input_text, title="Input", border_style="green"))

    def _update_output(self, layout: Layout, output: str = "") -> None:
        """Update the output panel with JSON plan or error."""
        if output:
            output_text = Text(output)
        else:
            output_text = Text("No output yet", style="gray")
        layout["output"].update(Panel(output_text, title="Output (JSON Plan)", border_style="yellow"))

    def _update_footer(self, layout: Layout) -> None:
        """Update the footer with recent logs."""
        logs = "\n".join(self.log_messages[-5:]) if self.log_messages else "No logs yet"
        log_text = Text(logs, style="dim")
        layout["footer"].update(Panel(log_text, title="Logs", border_style="dim"))

    def run_interactive(self) -> None:
        """Run the interactive TUI mode."""
        self.running = True
        
        # Start RAM monitoring
        from .ram_hardener import ram_hardener
        ram_hardener.start_monitoring(interval=2)
        
        layout = self._create_layout()
        
        console.print("[bold green]COM IDE Interactive Mode[/bold green]")
        console.print("Type 'quit' to exit\n")
        
        try:
            with Live(layout, console=console, refresh_per_second=4) as live:
                while self.running:
                    self._update_header(layout)
                    self._update_footer(layout)
                    
                    # Get user input
                    try:
                        user_input = console.input("[bold]Enter command:[/bold] ")
                    except EOFError:
                        break
                    
                    if user_input.lower() in ('quit', 'exit', 'q'):
                        break
                    
                    if not user_input.strip():
                        continue
                    
                    # Update input panel
                    self._update_input(layout, user_input)
                    
                    # Run pipeline
                    project_path = "."  # Default to current directory
                    result = self.pipeline.run(user_input, project_path)
                    
                    # Update state
                    self.last_output = str(result.get("plan", result.get("error", "Unknown")))
                    self.log_messages.append(f"Processed: {user_input[:30]}...")
                    
                    if result.get("model_used"):
                        self.current_model = result["model_used"]
                    
                    # Update panels
                    self._update_output(layout, self.last_output)
                    self._update_header(layout)
                    
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()

    def run_command(self, project_path: str, user_input: Optional[str] = None) -> None:
        """
        Run in command-line mode (non-interactive).
        
        Usage: com-ide run --project /path/to/godot "validate Player node path"
        """
        if not user_input:
            console.print("[red]Error: No input provided[/red]")
            sys.exit(1)
        
        console.print(f"[bold]Processing:[/bold] {user_input}")
        console.print(f"[bold]Project:[/bold] {project_path}\n")
        
        result = self.pipeline.run(user_input, project_path)
        
        if result.get("success"):
            console.print("[bold green]✓ Success[/bold green]")
            if result.get("cache_hit"):
                console.print("[dim](cached result)[/dim]")
            console.print(f"Model used: {result.get('model_used', 'unknown')}")
            console.print(f"Latency: {result.get('latency_ms', 0)}ms")
            console.print("\n[bold yellow]JSON Plan:[/bold yellow]")
            console.print_json(data=result.get("plan", {}))
        else:
            console.print("[bold red]✗ Failed[/bold red]")
            console.print(f"Error: {result.get('error', 'Unknown error')}")
            if result.get("fallback"):
                console.print(f"Fallback: {result['fallback']}")


def main():
    """Main entry point for the CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="COM IDE - Compiler-Lite Godot Assistant")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run the pipeline on a project")
    run_parser.add_argument("--project", "-p", required=True, help="Path to Godot project")
    run_parser.add_argument("input", nargs="?", help="User input/command")
    
    # Interactive command
    subparsers.add_parser("interactive", help="Run in interactive TUI mode")
    
    args = parser.parse_args()
    
    cli = ComIdeCLI()
    
    if args.command == "interactive":
        cli.run_interactive()
    elif args.command == "run":
        if not args.input:
            parser.error("run command requires an input argument")
        cli.run_command(args.project, args.input)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
