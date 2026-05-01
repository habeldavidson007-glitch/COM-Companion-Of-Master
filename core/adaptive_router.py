"""
Adaptive Router Module - liteLLM wrapper with RAM-aware fallback logic.

CRITICAL: This is the core engine that ensures operation on 2GB machines.
It dynamically selects models based on available RAM and handles OOM errors
by falling back to smaller models.

Logic Flow:
1. Check get_available_ram_gb()
2. Define model chain (largest to smallest)
3. Select first model where model.ram < (available_ram - SAFETY_BUFFER_GB)
4. Call liteLLM with selected model
5. If OOM error occurs, recursively try next smaller model
6. Enable streaming to reduce memory pressure
"""

from typing import Optional, Generator, Dict, Any, List
import sys

try:
    from litellm import completion as litellm_completion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    print("Warning: liteLLM not installed. AdaptiveRouter will use mock mode.", file=sys.stderr)

try:
    from config import MODEL_CHAIN, FALLBACK_MODEL, SAFETY_BUFFER_GB
except ImportError:
    # Fallback defaults if config is not available
    MODEL_CHAIN = [
        {"name": "qwen2.5-coder:7b", "ram": 4.5},
        {"name": "llama3.2:3b", "ram": 2.0},
        {"name": "smollm2:1.7b", "ram": 1.2},
    ]
    FALLBACK_MODEL = "smollm2:1.7b"
    SAFETY_BUFFER_GB = 1.5

from .ram_monitor import get_available_ram_gb, get_usable_ram_for_models, select_model_from_chain


class AdaptiveRouter:
    """
    Adaptive LLM router with RAM-aware model selection and fallback.
    
    This class wraps liteLLM.completion() with intelligent model selection
    based on real-time RAM availability. It automatically falls back to
    smaller models when larger ones cannot fit in memory.
    
    Attributes:
        model_chain: List of model configurations ordered by size.
        current_model: Currently selected model configuration.
        stream_enabled: Whether streaming is enabled for responses.
    
    Example:
        >>> router = AdaptiveRouter()
        >>> response = router.complete(
        ...     messages=[{"role": "user", "content": "Hello"}],
        ...     temperature=0.1
        ... )
        >>> print(response.choices[0].message.content)
    """
    
    def __init__(self, model_chain: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize the adaptive router.
        
        Args:
            model_chain: Optional override for model chain. Uses config.MODEL_CHAIN
                        if not provided. Should be ordered largest to smallest.
        """
        self.model_chain = model_chain if model_chain else MODEL_CHAIN
        self.current_model: Optional[Dict[str, Any]] = None
        self.stream_enabled = True
        self._selected_model_index = 0
    
    def select_best_model(self) -> Optional[Dict[str, Any]]:
        """
        Select the best model based on current RAM availability.
        
        Returns:
            dict or None: Selected model configuration, or None if no model fits.
        
        Side Effects:
            Updates self.current_model and logs the selection.
        """
        usable_ram = get_usable_ram_for_models()
        
        # Find first model that fits
        for i, model in enumerate(self.model_chain):
            model_name = model.get("name", "unknown")
            model_ram = model.get("ram", 0)
            
            if model_ram <= usable_ram:
                self.current_model = model
                self._selected_model_index = i
                return model
        
        # No model fits - return fallback if available
        if self.model_chain:
            # Use smallest model as last resort
            self.current_model = self.model_chain[-1]
            self._selected_model_index = len(self.model_chain) - 1
            return self.current_model
        
        return None
    
    def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 512,
        top_p: float = 0.9,
        **kwargs
    ) -> Any:
        """
        Complete a chat request using the best available model.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature (default: 0.1 for deterministic output).
            max_tokens: Maximum tokens to generate.
            top_p: Nucleus sampling parameter.
            **kwargs: Additional arguments passed to liteLLM.
        
        Returns:
            Response object from liteLLM (or mock response if liteLLM unavailable).
        
        Raises:
            RuntimeError: If no model can be loaded and all fallbacks fail.
        """
        # Select best model for current RAM state
        model_config = self.select_best_model()
        
        if model_config is None:
            raise RuntimeError(
                f"No model available. Usable RAM: {get_usable_ram_for_models():.2f} GB. "
                f"Smallest model requires: {self.model_chain[-1]['ram']:.2f} GB"
            )
        
        model_name = model_config["name"]
        
        # Log model selection (in production, use logfire)
        print(f"[AdaptiveRouter] Selected model: {model_name}", file=sys.stderr)
        
        if not LITELLM_AVAILABLE:
            # Mock mode for testing without liteLLM
            return self._mock_complete(messages, model_name, temperature, max_tokens)
        
        # Try completion with selected model
        try:
            return self._call_litellm(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=self.stream_enabled,
                **kwargs
            )
        except Exception as e:
            # Handle OOM or other errors by trying next smaller model
            return self._handle_error_and_fallback(
                messages, temperature, max_tokens, top_p, e, **kwargs
            )
    
    def _call_litellm(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float,
        stream: bool,
        **kwargs
    ) -> Any:
        """
        Internal method to call liteLLM completion.
        
        Args:
            model: Model name string.
            messages: Chat messages.
            temperature: Sampling temperature.
            max_tokens: Max generation tokens.
            top_p: Nucleus sampling.
            stream: Enable streaming.
            **kwargs: Additional args.
        
        Returns:
            liteLLM response object.
        """
        return litellm_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=stream,
            **kwargs
        )
    
    def _handle_error_and_fallback(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float,
        error: Exception,
        **kwargs
    ) -> Any:
        """
        Handle errors by attempting to fall back to smaller models.
        
        Args:
            messages: Original chat messages.
            temperature: Sampling temperature.
            max_tokens: Max generation tokens.
            top_p: Nucleus sampling.
            error: The exception that triggered fallback.
            **kwargs: Additional args.
        
        Returns:
            Response from fallback model, or re-raises if all fallbacks fail.
        
        Raises:
            RuntimeError: If all models in chain have been exhausted.
        """
        error_msg = str(error)
        is_oom = "out of memory" in error_msg.lower() or "oom" in error_msg.lower()
        
        print(
            f"[AdaptiveRouter] Error with {self.current_model['name']}: {error_msg}",
            file=sys.stderr
        )
        
        # Try next smaller model
        next_index = self._selected_model_index + 1
        
        if next_index >= len(self.model_chain):
            # No more models to try
            raise RuntimeError(
                f"All models exhausted. Last error: {error_msg}"
            ) from error
        
        # Update to next model and retry
        print(
            f"[AdaptiveRouter] Falling back to: {self.model_chain[next_index]['name']}",
            file=sys.stderr
        )
        
        self.current_model = self.model_chain[next_index]
        self._selected_model_index = next_index
        
        # Recursive retry with smaller model
        return self.complete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            **kwargs
        )
    
    def complete_streaming(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 512,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream completion tokens one at a time.
        
        This method yields tokens as they are generated, reducing memory
        pressure by not buffering the entire response.
        
        Args:
            messages: Chat messages.
            temperature: Sampling temperature.
            max_tokens: Max generation tokens.
            **kwargs: Additional args.
        
        Yields:
            Generated token strings.
        """
        self.stream_enabled = True
        response = self.complete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        if not LITELLM_AVAILABLE:
            # Mock streaming
            mock_response = self._mock_complete(messages, "mock", temperature, max_tokens)
            yield mock_response
            return
        
        # Iterate over streaming response
        for chunk in response:
            if hasattr(chunk, "choices") and chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    yield delta.content
    
    def _mock_complete(
        self,
        messages: List[Dict[str, str]],
        model_name: str,
        temperature: float,
        max_tokens: int
    ) -> Any:
        """
        Mock completion for testing without liteLLM.
        
        Returns a simple response object structure similar to liteLLM.
        """
        class MockChoice:
            def __init__(self, content: str):
                self.message = type('obj', (object,), {'content': content})()
                self.finish_reason = "stop"
        
        class MockResponse:
            def __init__(self, content: str):
                self.choices = [MockChoice(content)]
                self.model = model_name
        
        last_message = messages[-1]["content"] if messages else ""
        content = f"[Mock {model_name}] Received: {last_message[:50]}..."
        
        return MockResponse(content)


# Convenience function for simple usage
def adaptive_complete(
    messages: List[Dict[str, str]],
    temperature: float = 0.1,
    max_tokens: int = 512,
    **kwargs
) -> Any:
    """
    Convenience function for adaptive completion.
    
    Creates a temporary router and completes the request.
    For repeated use, instantiate AdaptiveRouter directly.
    
    Args:
        messages: Chat messages.
        temperature: Sampling temperature.
        max_tokens: Max generation tokens.
        **kwargs: Additional args.
    
    Returns:
        Response from adaptive router.
    """
    router = AdaptiveRouter()
    return router.complete(messages, temperature, max_tokens, **kwargs)


if __name__ == "__main__":
    # Test the adaptive router
    print("=" * 50)
    print("AdaptiveRouter Test")
    print("=" * 50)
    
    router = AdaptiveRouter()
    print(f"Selected model: {router.current_model}")
    
    test_messages = [{"role": "user", "content": "What is Godot?"}]
    
    try:
        response = router.complete(test_messages, temperature=0.1)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("=" * 50)
