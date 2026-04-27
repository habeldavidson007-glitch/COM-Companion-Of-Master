#!/usr/bin/env python3
"""COM CLI Entry Point"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from com.core.com_core import COMCore

def main():
    if len(sys.argv) < 2:
        print("Usage: com_cli.py <command>")
        sys.exit(1)
    
    command = " ".join(sys.argv[1:])
    core = COMCore()
    response = core.process(command)
    print(response)

if __name__ == "__main__":
    main()
