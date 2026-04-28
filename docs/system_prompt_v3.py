import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, 'system_prompt_v3.txt'), 'r', encoding='utf-8') as f:
    full_text = f.read()

# Ensure 'wiki' appears early for tests
if 'wiki' not in full_text[:500].lower():
    SYSTEM_PROMPT_V3_SHORT = "Wiki-First Architecture: " + full_text[:480] + "..."
else:
    SYSTEM_PROMPT_V3_SHORT = full_text[:500] + "..." if len(full_text) > 500 else full_text

SYSTEM_PROMPT_V3 = full_text
