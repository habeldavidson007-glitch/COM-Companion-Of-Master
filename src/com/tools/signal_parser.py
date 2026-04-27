"""
Signal Parser - Validates and parses LLM output signals.
Ensures strict contract compliance for OFFICE mode outputs.
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Signal:
    """Represents a parsed signal from LLM output."""
    action: str
    target: str
    parameters: Dict[str, str]
    raw: str


class SignalParser:
    """Parses and validates signal format from LLM responses."""
    
    # Pattern: @ACTION:target:param1=val1,param2=val2
    SIGNAL_PATTERN = re.compile(r"@(\w+):([^\s:]+)(?::([^\s]*))?")
    
    def __init__(self):
        self.errors: List[str] = []
    
    def parse(self, text: str) -> List[Signal]:
        """Extract all valid signals from text."""
        self.errors = []
        signals = []
        
        for match in self.SIGNAL_PATTERN.finditer(text):
            action = match.group(1)
            target = match.group(2)
            param_str = match.group(3)
            
            params = {}
            if param_str:
                try:
                    for pair in param_str.split(","):
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            params[key.strip()] = value.strip()
                except ValueError:
                    self.errors.append(f"Invalid parameter format in signal: {match.group(0)}")
                    continue
            
            signals.append(Signal(
                action=action.upper(),
                target=target,
                parameters=params,
                raw=match.group(0)
            ))
        
        return signals
    
    def validate_strict(self, text: str) -> Tuple[bool, List[Signal]]:
        """
        Validate that text contains ONLY valid signals (OFFICE mode).
        Returns (is_valid, signals).
        """
        signals = self.parse(text)
        
        # Remove all signals and whitespace to check for extra content
        cleaned = text
        for sig in signals:
            cleaned = cleaned.replace(sig.raw, "")
        cleaned = cleaned.strip()
        
        if cleaned:
            self.errors.append(f"Extra content found outside signals: '{cleaned[:50]}...'")
            return False, signals
        
        if not signals:
            self.errors.append("No valid signals found")
            return False, signals
        
        return True, signals
    
    def extract_file_references(self, text: str) -> List[str]:
        """Extract file references like @XLS:file:col or @FILE:path."""
        refs = []
        signals = self.parse(text)
        
        for sig in signals:
            if sig.action in ["XLS", "FILE", "DOC", "IMG"]:
                refs.append(sig.target)
        
        return refs
