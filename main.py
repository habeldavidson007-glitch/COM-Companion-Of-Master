"""
COM v4 - Main Entry Point

Demonstrates the cognitive architecture in action.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core import CognitiveAgent, ContextManager, ReflectionEngine
from tools import SecureExecutor, WikiCompiler


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def compile_knowledge():
    """Compile knowledge base on startup."""
    print("Compiling knowledge base...")
    compiler = WikiCompiler()
    chunks = compiler.compile_all()
    print(f"Compiled {len(chunks)} knowledge chunks")
    return len(chunks) > 0


def interactive_mode(agent: CognitiveAgent):
    """Run interactive chat mode."""
    print("\n" + "="*60)
    print("COM v4 Cognitive Agent - Interactive Mode")
    print("="*60)
    print("Commands:")
    print("  /quit     - Exit the program")
    print("  /clear    - Clear conversation history")
    print("  /stats    - Show context statistics")
    print("  /compile  - Recompile knowledge base")
    print("="*60 + "\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() == '/quit':
                print("Goodbye!")
                break
            
            elif user_input.lower() == '/clear':
                agent.context_manager.clear_history()
                print("Conversation history cleared.")
                continue
            
            elif user_input.lower() == '/stats':
                stats = agent.context_manager.get_stats()
                print("\nContext Statistics:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
                print()
                continue
            
            elif user_input.lower() == '/compile':
                compile_knowledge()
                continue
            
            # Process query
            print("\nThinking...", end="", flush=True)
            response = agent.run(user_input)
            
            print(f"\n\nCOM v4: {response.answer}")
            print(f"\n[Confidence: {response.confidence:.2f}, "
                  f"Reflections: {response.required_reflections}, "
                  f"Tools: {', '.join(response.tools_used) if response.tools_used else 'None'}]")
            print("-"*60 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type /quit to exit.")
            continue
        except Exception as e:
            print(f"\nError: {e}")
            logging.exception("Error processing query")


def demo_mode(agent: CognitiveAgent):
    """Run demonstration queries."""
    demo_queries = [
        "What is 15 * 23 + 48 / 6?",
        "Explain the water cycle in simple terms.",
        "Write Python code to calculate factorial of 5.",
    ]
    
    print("\n" + "="*60)
    print("COM v4 Cognitive Agent - Demo Mode")
    print("="*60 + "\n")
    
    for i, query in enumerate(demo_queries, 1):
        print(f"Query {i}: {query}")
        print("-"*40)
        
        response = agent.run(query)
        
        print(f"Answer: {response.answer}")
        print(f"Confidence: {response.confidence:.2f}")
        print(f"Thought Steps: {len(response.thought_chain)}")
        print(f"Reflections: {response.required_reflections}")
        print()


def main():
    """Main entry point."""
    setup_logging()
    
    print("="*60)
    print("COM v4 - Cognitive Architecture")
    print("Making 1.5B models perform at 7B+ levels")
    print("="*60 + "\n")
    
    # Compile knowledge base
    has_knowledge = compile_knowledge()
    if not has_knowledge:
        print("Warning: No knowledge base compiled. Add files to knowledge/raw/")
    
    # Initialize components
    print("\nInitializing cognitive engine...")
    context_manager = ContextManager()
    reflection_engine = ReflectionEngine()
    
    # Create secure executor tool
    secure_executor = SecureExecutor()
    
    # Define available tools
    tools = {
        "execute_code": lambda code: secure_executor.execute(code),
        "wiki_search": lambda query: [
            chunk.content for chunk in context_manager.inject_wiki_context(query)
        ],
    }
    
    # Create agent
    agent = CognitiveAgent(
        model_name="com-v4-cognitive",
        tools=tools,
        context_manager=context_manager,
        reflection_engine=reflection_engine
    )
    
    print("Cognitive engine ready!\n")
    
    # Determine mode
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_mode(agent)
    else:
        interactive_mode(agent)


if __name__ == "__main__":
    main()
