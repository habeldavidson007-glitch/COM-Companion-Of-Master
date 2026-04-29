"""
COM v3 Wiki Viewer - Simple Prototype
======================================
Toggle views between data/raw/, data/wiki/, and data/com_output/
Available as CLI or basic Streamlit web interface.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


class WikiViewer:
    """Simple file viewer for COM v3 data directories."""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.wiki_dir = self.data_dir / "wiki"
        self.output_dir = self.data_dir / "com_output"
        
        # Ensure directories exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.wiki_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def list_files(self, directory: Path, pattern: str = "*") -> List[Path]:
        """List files in a directory matching pattern."""
        if not directory.exists():
            return []
        return sorted(directory.glob(pattern))
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get information about a file."""
        if not file_path.exists():
            return {"error": "File not found"}
        
        stat = file_path.stat()
        return {
            "name": file_path.name,
            "path": str(file_path),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "extension": file_path.suffix,
            "readable_size": self._format_size(stat.st_size)
        }
    
    def read_file_content(self, file_path: Path, max_lines: int = 100) -> str:
        """Read file content with line limit."""
        if not file_path.exists():
            return "Error: File not found"
        
        try:
            if file_path.suffix in ['.pdf', '.xlsx', '.pptx', '.bin']:
                return f"[Binary file: {file_path.suffix}]"
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append(f"\n... (truncated at {max_lines} lines)")
                        break
                    lines.append(line)
                return ''.join(lines)
        except Exception as e:
            return f"Error reading file: {e}"
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def get_directory_summary(self, directory: Path) -> Dict[str, Any]:
        """Get summary statistics for a directory."""
        if not directory.exists():
            return {"error": "Directory not found"}
        
        files = self.list_files(directory)
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        extensions = {}
        
        for f in files:
            if f.is_file():
                ext = f.suffix or "(no extension)"
                extensions[ext] = extensions.get(ext, 0) + 1
        
        return {
            "path": str(directory),
            "file_count": len(files),
            "total_size": self._format_size(total_size),
            "extensions": extensions,
            "files": [self.get_file_info(f) for f in files[:20]]  # Limit to first 20
        }
    
    def view_raw(self) -> Dict[str, Any]:
        """View raw data directory."""
        return self.get_directory_summary(self.raw_dir)
    
    def view_wiki(self) -> Dict[str, Any]:
        """View wiki directory."""
        return self.get_directory_summary(self.wiki_dir)
    
    def view_output(self) -> Dict[str, Any]:
        """View output directory."""
        return self.get_directory_summary(self.output_dir)
    
    def search_wiki(self, query: str) -> List[Dict]:
        """Simple search in wiki files."""
        results = []
        wiki_files = self.list_files(self.wiki_dir, "*.md")
        
        for file_path in wiki_files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='replace').lower()
                if query.lower() in content:
                    # Find context around match
                    idx = content.find(query.lower())
                    start = max(0, idx - 100)
                    end = min(len(content), idx + len(query) + 100)
                    snippet = content[start:end].replace('\n', ' ').strip()
                    
                    results.append({
                        "file": str(file_path),
                        "snippet": f"...{snippet}...",
                        "match_position": idx
                    })
            except Exception:
                continue
        
        return results[:10]  # Limit results
    
    def print_tree(self, directory: Path = None, prefix: str = "", max_depth: int = 3) -> str:
        """Print directory tree structure."""
        if directory is None:
            directory = self.data_dir
        
        lines = []
        
        def _tree_recursive(current_dir: Path, current_prefix: str, depth: int):
            if depth > max_depth:
                return
            
            items = sorted([p for p in current_dir.iterdir() if not p.name.startswith('.')])
            
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                
                if item.is_file():
                    size = self._format_size(item.stat().st_size)
                    lines.append(f"{current_prefix}{connector}{item.name} ({size})")
                elif item.is_dir():
                    lines.append(f"{current_prefix}{connector}{item.name}/")
                    new_prefix = current_prefix + ("    " if is_last else "│   ")
                    _tree_recursive(item, new_prefix, depth + 1)
        
        lines.append(f"{directory.name}/")
        _tree_recursive(directory, "", 1)
        
        return "\n".join(lines)


def cli_viewer():
    """Command-line interface for WikiViewer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="COM v3 Wiki Viewer")
    parser.add_argument("--data-dir", default="./data", help="Data directory path")
    parser.add_argument("--view", choices=["raw", "wiki", "output", "all"], default="all",
                       help="Which directory to view")
    parser.add_argument("--search", type=str, help="Search query for wiki")
    parser.add_argument("--tree", action="store_true", help="Show directory tree")
    parser.add_argument("--preview", type=str, help="Preview specific file")
    
    args = parser.parse_args()
    
    viewer = WikiViewer(data_dir=args.data_dir)
    
    if args.search:
        print(f"Searching wiki for: '{args.search}'")
        print("=" * 60)
        results = viewer.search_wiki(args.search)
        if results:
            for result in results:
                print(f"\n📄 {result['file']}")
                print(f"   {result['snippet']}")
        else:
            print("No results found.")
        return
    
    if args.preview:
        file_path = Path(args.preview)
        if not file_path.is_absolute():
            # Try to find in data directories
            for base_dir in [viewer.raw_dir, viewer.wiki_dir, viewer.output_dir]:
                candidate = base_dir / file_path
                if candidate.exists():
                    file_path = candidate
                    break
        
        print(f"Previewing: {file_path}")
        print("=" * 60)
        content = viewer.read_file_content(file_path)
        print(content)
        return
    
    if args.tree:
        print("Data Directory Structure:")
        print("=" * 60)
        print(viewer.print_tree())
        return
    
    # Default: show summaries
    if args.view in ["raw", "all"]:
        print("\n📁 RAW DATA DIRECTORY")
        print("=" * 60)
        raw_summary = viewer.view_raw()
        if "error" not in raw_summary:
            print(f"Files: {raw_summary['file_count']}")
            print(f"Total Size: {raw_summary['total_size']}")
            print(f"Extensions: {raw_summary['extensions']}")
            if raw_summary['files']:
                print("\nRecent Files:")
                for f in raw_summary['files'][:5]:
                    print(f"  • {f['name']} ({f['readable_size']})")
    
    if args.view in ["wiki", "all"]:
        print("\n📚 WIKI DIRECTORY")
        print("=" * 60)
        wiki_summary = viewer.view_wiki()
        if "error" not in wiki_summary:
            print(f"Articles: {wiki_summary['file_count']}")
            print(f"Total Size: {wiki_summary['total_size']}")
            print(f"Extensions: {wiki_summary['extensions']}")
            if wiki_summary['files']:
                print("\nRecent Articles:")
                for f in wiki_summary['files'][:5]:
                    print(f"  • {f['name']} ({f['readable_size']})")
    
    if args.view in ["output", "all"]:
        print("\n📤 OUTPUT DIRECTORY")
        print("=" * 60)
        output_summary = viewer.view_output()
        if "error" not in output_summary:
            print(f"Files: {output_summary['file_count']}")
            print(f"Total Size: {output_summary['total_size']}")
            print(f"Extensions: {output_summary['extensions']}")
            if output_summary['files']:
                print("\nRecent Outputs:")
                for f in output_summary['files'][:5]:
                    print(f"  • {f['name']} ({f['readable_size']})")


def streamlit_viewer():
    """Streamlit web interface for WikiViewer."""
    try:
        import streamlit as st
    except ImportError:
        print("Streamlit not installed. Install with: pip install streamlit")
        print("Falling back to CLI mode...")
        cli_viewer()
        return
    
    st.set_page_config(page_title="COM v3 Wiki Viewer", layout="wide")
    st.title("🧠 COM v3 Wiki Viewer")
    
    viewer = WikiViewer()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    view_choice = st.sidebar.radio(
        "Select View:",
        ["Overview", "Raw Data", "Wiki", "Output", "Search", "Tree View"]
    )
    
    if view_choice == "Overview":
        st.header("📊 Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            raw = viewer.view_raw()
            st.metric("Raw Files", raw.get('file_count', 0))
        
        with col2:
            wiki = viewer.view_wiki()
            st.metric("Wiki Articles", wiki.get('file_count', 0))
        
        with col3:
            output = viewer.view_output()
            st.metric("Output Files", output.get('file_count', 0))
        
        st.subheader("Quick Stats")
        st.json({
            "raw": viewer.view_raw(),
            "wiki": viewer.view_wiki(),
            "output": viewer.view_output()
        })
    
    elif view_choice == "Raw Data":
        st.header("📁 Raw Data")
        raw_data = viewer.view_raw()
        
        if raw_data.get('files'):
            st.dataframe(raw_data['files'])
            
            # File preview
            selected = st.selectbox("Preview File:", [f['name'] for f in raw_data['files']])
            if selected:
                file_path = next(f['path'] for f in raw_data['files'] if f['name'] == selected)
                content = viewer.read_file_content(Path(file_path))
                st.code(content, language="text")
    
    elif view_choice == "Wiki":
        st.header("📚 Wiki Knowledge Base")
        wiki_data = viewer.view_wiki()
        
        if wiki_data.get('files'):
            st.dataframe(wiki_data['files'])
            
            # Article preview
            selected = st.selectbox("Preview Article:", [f['name'] for f in wiki_data['files']])
            if selected:
                file_path = next(f['path'] for f in wiki_data['files'] if f['name'] == selected)
                content = viewer.read_file_content(Path(file_path))
                st.markdown(content)
    
    elif view_choice == "Output":
        st.header("📤 Generated Output")
        output_data = viewer.view_output()
        
        if output_data.get('files'):
            st.dataframe(output_data['files'])
    
    elif view_choice == "Search":
        st.header("🔍 Search Wiki")
        query = st.text_input("Search Query:")
        
        if query:
            results = viewer.search_wiki(query)
            if results:
                for result in results:
                    with st.expander(f"📄 {Path(result['file']).name}"):
                        st.write(result['snippet'])
                        st.write(f"**Full Path:** `{result['file']}`")
            else:
                st.info("No results found.")
    
    elif view_choice == "Tree View":
        st.header("🌳 Directory Structure")
        tree = viewer.print_tree()
        st.text(tree)


if __name__ == "__main__":
    # Check if running with streamlit
    if len(sys.argv) > 1 and sys.argv[1] == "--web":
        streamlit_viewer()
    else:
        cli_viewer()
