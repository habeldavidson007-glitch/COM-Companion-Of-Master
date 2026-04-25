"""
Context Compressor: Summarizes old conversation turns to save RAM.
Keeps semantic history alive without growing context window.
"""

class ContextCompressor:
    """
    When history hits max, compress oldest 4 messages into
    one summary message instead of dropping them silently.
    Keeps knowledge alive without growing context window.
    """
    
    COMPRESS_PROMPT = """Summarize this conversation in max 2 sentences.
Keep only: decisions made, facts stated, tasks done.
Output: plain text, no bullet points."""

    def __init__(self, client=None):
        self.client = client

    def compress(self, messages: list) -> dict | None:
        """
        Compresses the first 4 messages into a single summary.
        Returns a system message with the summary, or None if not enough messages.
        """
        if not self.client or len(messages) < 4:
            return None
            
        to_compress = messages[:4]
        text = "\n".join([f"{m['role']}: {m['content']}" for m in to_compress])
        
        try:
            summary = self.client.generate(
                [{"role": "user", "content": f"{self.COMPRESS_PROMPT}\n\n{text}"}],
                max_tokens=60,
                temperature=0.1
            )
            return {"role": "system", "content": f"[Prior context]: {summary}"}
        except Exception:
            return None
