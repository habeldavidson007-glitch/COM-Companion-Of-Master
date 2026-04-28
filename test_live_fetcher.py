#!/usr/bin/env python3
"""
Test script for LiveFetcher module.
Demonstrates fetching from URLs, local files, and git repos.
"""

from tools.data_ops.live_fetcher import LiveFetcher

def main():
    # Initialize
    fetcher = LiveFetcher(raw_dir="data/raw", wiki_dir="data/wiki")
    
    print("=" * 60)
    print("COM v3 - LiveFetcher Test Suite")
    print("=" * 60)
    
    # Test 1: Fetch a Web URL (e.g., ArXiv abstract)
    print("\n--- Test 1: Web URL Fetch ---")
    result = fetcher.fetch(
        "https://arxiv.org/abs/2301.00001", 
        source_type="url", 
        title="LLM Survey Paper"
    )
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"✓ Saved to: {result['wiki_path']}")
        print(f"✓ Title: {result['title']}")
    else:
        print(f"✗ Error: {result['message']}")

    # Test 2: Fetch a Local File (Create a test file first)
    print("\n--- Test 2: Local File Fetch ---")
    test_file = Path("data/raw/test_notes.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("# Test Notes\n\nThis is a test document for COM v3.\n\n## Key Points\n- Point 1\n- Point 2")
    
    result = fetcher.fetch(str(test_file), source_type="file")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"✓ Saved to: {result['wiki_path']}")
    else:
        print(f"✗ Error: {result['message']}")

    # Test 3: Fetch a Git Repo (e.g., a small library README)
    print("\n--- Test 3: Git Repo Fetch ---")
    result = fetcher.fetch("https://github.com/psf/requests.git", source_type="git")
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"✓ Saved to: {result['wiki_path']}")
        print(f"✓ Title: {result['title']}")
    else:
        print(f"✗ Error: {result['message']}")
    
    print("\n" + "=" * 60)
    print("Test Suite Complete")
    print("=" * 60)

if __name__ == "__main__":
    from pathlib import Path
    main()
