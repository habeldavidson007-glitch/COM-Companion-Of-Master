# Auto-generated stub for system_prompt_v3
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, 'system_prompt_v3.txt'), 'r', encoding='utf-8') as f:
    SYSTEM_PROMPT_V3 = f.read()
SYSTEM_PROMPT_V3_SHORT = SYSTEM_PROMPT_V3[:500] + "..." if len(SYSTEM_PROMPT_V3) > 500 else SYSTEM_PROMPT_V3
