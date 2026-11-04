# v2/src/main.py
import sys
import os

# Add project root to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from v2.src.core.orchestrator import SuperRAGSystem

def main():
    """Main application entry point"""
    # Initialize super enhanced system
    rag_system = SuperRAGSystem()
    
    print("\n" + "="*60)
    print("🎯 SUPER ENHANCED RAG ASSISTANT - V2")
    print("="*60)
    
    # System setup
    rag_system.setup_system(clear_existing=False)
    
    print("\n✨ FEATURES ACTIVATED:")
    print("• Multi-AI Model Support")
    print("• Web Search Integration")
    print("• Google Workspace Integration")
    print("• RAG Document Search")
    
    # Main interaction loop
    while True:
        try:
            user_input = input("\n🧠 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye', '/quit']:
                print("👋 Thank you for using RAG Assistant V2!")
                break
                
            if not user_input:
                continue
            
            # Process the query
            response = rag_system.handle_query_enhanced(user_input)
            
            if response:
                print(f"\n🤖 Assistant: {response}")
                print("-" * 60)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Session interrupted. Type 'quit' to exit.")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
