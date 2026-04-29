"""
Background Service - Low-RAM Daemon for COM v3 Wiki Maintenance
================================================================
Runs every 30 minutes to perform health checks and maintenance tasks.
Non-blocking, thread-safe, suitable for low-RAM environments.
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from tools.data_ops.wiki_compiler import WikiCompiler, WikiRetriever, HealthChecker
from tools.data_ops.wiki_indexer import WikiIndexer


class BackgroundWikiService:
    """
    Low-RAM background daemon for wiki maintenance.
    Runs periodic health checks without blocking main application.
    """
    
    def __init__(self, data_dir: str = "./data", check_interval_minutes: int = 30):
        self.data_dir = Path(data_dir)
        self.check_interval = timedelta(minutes=check_interval_minutes)
        
        # Initialize wiki components
        self.compiler = WikiCompiler(data_dir=str(data_dir))
        self.indexer = WikiIndexer(data_dir=str(data_dir))
        self.retriever = WikiRetriever(data_dir=str(data_dir))
        self.health_checker = HealthChecker(wiki_dir=str(self.data_dir / "wiki"))
        
        # Service state
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_check_time: Optional[datetime] = None
        self.last_check_results: Dict[str, Any] = {}
        
        # Performance settings for low-RAM
        self.max_concurrent_checks = 1
        self.batch_size = 5  # Process items in small batches
        
    def start(self):
        """Start the background service."""
        if self.running:
            logger.warning("Background service already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._service_loop, daemon=True, name="WikiBackgroundService")
        self.thread.start()
        logger.info(f"Background wiki service started (interval: {self.check_interval})")
    
    def stop(self):
        """Stop the background service gracefully."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        logger.info("Background wiki service stopped")
    
    def _service_loop(self):
        """Main service loop - runs periodically."""
        while self.running:
            try:
                self._run_maintenance_cycle()
                self.last_check_time = datetime.now()
            except Exception as e:
                logger.error(f"Error in maintenance cycle: {e}")
            
            # Sleep in small increments to allow quick shutdown
            sleep_seconds = self.check_interval.total_seconds()
            for _ in range(int(sleep_seconds)):
                if not self.running:
                    break
                time.sleep(1)
    
    def _run_maintenance_cycle(self):
        """Run a complete maintenance cycle."""
        logger.info("Starting wiki maintenance cycle...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "tasks_run": [],
            "issues_found": [],
            "suggestions": []
        }
        
        # Task 1: Health Check - Find broken links
        logger.info("Task 1: Running integrity check...")
        integrity_issues = self._check_integrity()
        results["tasks_run"].append("integrity_check")
        results["issues_found"].extend(integrity_issues)
        
        # Task 2: Find orphaned documents
        logger.info("Task 2: Finding orphaned documents...")
        orphans = self._find_orphans()
        results["tasks_run"].append("orphan_check")
        if orphans:
            results["issues_found"].append({
                "type": "orphans",
                "count": len(orphans),
                "documents": orphans[:10]  # Limit to first 10
            })
        
        # Task 3: Suggest new connections
        logger.info("Task 3: Analyzing for new connections...")
        suggestions = self._suggest_connections()
        results["tasks_run"].append("connection_analysis")
        results["suggestions"].extend(suggestions)
        
        # Task 4: Compile any new raw files
        logger.info("Task 4: Checking for new raw files to compile...")
        compiled = self._compile_new_files()
        results["tasks_run"].append("incremental_compile")
        if compiled:
            results["compiled_count"] = len(compiled)
        
        # Store results
        self.last_check_results = results
        
        # Log summary
        issue_count = len(results["issues_found"])
        suggestion_count = len(results["suggestions"])
        logger.info(
            f"Maintenance cycle complete: {issue_count} issues, "
            f"{suggestion_count} suggestions, {compiled} files compiled"
        )
    
    def _check_integrity(self) -> List[Dict]:
        """Check for broken links and missing files."""
        issues = []
        
        try:
            # Run async health check
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                integrity_issues = loop.run_until_complete(
                    self.health_checker.run_integrity_check()
                )
                issues.extend(integrity_issues)
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Integrity check failed: {e}")
            issues.append({
                "type": "check_error",
                "message": str(e),
                "severity": "high"
            })
        
        return issues
    
    def _find_orphans(self) -> List[str]:
        """Find documents with no backlinks."""
        try:
            return self.indexer.find_orphans()
        except Exception as e:
            logger.error(f"Orphan check failed: {e}")
            return []
    
    def _suggest_connections(self) -> List[Dict]:
        """Analyze wiki and suggest new connections between documents."""
        suggestions = []
        
        try:
            # Get all documents
            docs = list(self.indexer.index.get("documents", {}).keys())
            
            # Simple heuristic: documents with similar concepts might be related
            concept_map = self.indexer.index.get("concepts", {})
            
            for concept, doc_ids in concept_map.items():
                if len(doc_ids) > 1:
                    # Multiple documents share this concept - suggest cross-linking
                    suggestions.append({
                        "type": "concept_cluster",
                        "concept": concept,
                        "documents": doc_ids[:5],  # Limit
                        "suggestion": f"Consider adding cross-references between these {len(doc_ids)} documents about '{concept}'"
                    })
            
            # Limit suggestions
            return suggestions[:10]
            
        except Exception as e:
            logger.error(f"Connection analysis failed: {e}")
            return []
    
    def _compile_new_files(self) -> int:
        """Compile any new raw files that haven't been processed."""
        try:
            results = self.compiler.compile_all(incremental=True)
            return len(results)
        except Exception as e:
            logger.error(f"Incremental compilation failed: {e}")
            return 0
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status."""
        return {
            "running": self.running,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None,
            "next_check": (
                (self.last_check_time + self.check_interval).isoformat()
                if self.last_check_time else None
            ),
            "interval_minutes": self.check_interval.total_seconds() / 60,
            "last_results_summary": {
                "issues_count": len(self.last_check_results.get("issues_found", [])),
                "suggestions_count": len(self.last_check_results.get("suggestions", [])),
                "tasks_run": self.last_check_results.get("tasks_run", [])
            } if self.last_check_results else None
        }
    
    def run_manual_check(self) -> Dict[str, Any]:
        """Run a manual maintenance check immediately."""
        logger.info("Running manual maintenance check...")
        self._run_maintenance_cycle()
        return self.last_check_results


class WikiMaintenanceDaemon:
    """
    System-level daemon wrapper for the background service.
    Can be run as a standalone script or imported as a module.
    """
    
    def __init__(self, data_dir: str = "./data", interval_minutes: int = 30):
        self.service = BackgroundWikiService(
            data_dir=data_dir,
            check_interval_minutes=interval_minutes
        )
        self.started_at: Optional[datetime] = None
    
    def start_daemon(self):
        """Start the daemon."""
        self.started_at = datetime.now()
        self.service.start()
        print(f"✓ Wiki Maintenance Daemon started at {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✓ Check interval: {self.service.check_interval}")
        print(f"✓ Data directory: {self.service.data_dir}")
        print("\nPress Ctrl+C to stop...")
    
    def stop_daemon(self):
        """Stop the daemon gracefully."""
        self.service.stop()
        uptime = datetime.now() - self.started_at if self.started_at else timedelta(0)
        print(f"\n✓ Daemon stopped (uptime: {uptime})")
    
    def get_status_report(self) -> str:
        """Generate a human-readable status report."""
        status = self.service.get_status()
        
        lines = [
            "=" * 50,
            "COM v3 Wiki Maintenance Daemon Status",
            "=" * 50,
            f"Running: {status['running']}",
            f"Interval: {status['interval_minutes']} minutes",
            f"Last Check: {status['last_check'] or 'Never'}",
            f"Next Check: {status['next_check'] or 'Pending'}",
        ]
        
        if status['last_results_summary']:
            summary = status['last_results_summary']
            lines.extend([
                "",
                "Last Check Results:",
                f"  Issues Found: {summary['issues_count']}",
                f"  Suggestions: {summary['suggestions_count']}",
                f"  Tasks Run: {', '.join(summary['tasks_run'])}"
            ])
        
        lines.append("=" * 50)
        return "\n".join(lines)


def main():
    """Main entry point for running as a standalone daemon."""
    import argparse
    
    parser = argparse.ArgumentParser(description="COM v3 Wiki Maintenance Daemon")
    parser.add_argument(
        "--data-dir", 
        default="./data",
        help="Data directory path (default: ./data)"
    )
    parser.add_argument(
        "--interval", 
        type=int, 
        default=30,
        help="Check interval in minutes (default: 30)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show status and exit"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (no daemon mode)"
    )
    
    args = parser.parse_args()
    
    daemon = WikiMaintenanceDaemon(
        data_dir=args.data_dir,
        interval_minutes=args.interval
    )
    
    if args.status:
        print(daemon.get_status_report())
        return
    
    if args.once:
        print("Running single maintenance cycle...")
        results = daemon.service.run_manual_check()
        print(f"Completed: {results['tasks_run']}")
        print(f"Issues found: {len(results['issues_found'])}")
        print(f"Suggestions: {len(results['suggestions'])}")
        return
    
    # Start daemon mode
    try:
        daemon.start_daemon()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        daemon.stop_daemon()


if __name__ == "__main__":
    main()
