# v2/src/core/orchestrator.py
import sys
import time
from datetime import datetime

# Import modular components
try:
    from v2.src.core.rag import EnhancedDocumentProcessor
    from v2.src.core.memory import ConversationManager
    from v2.src.core.llm import ModelManager
    from v2.src.services.web import WebSearchManager
    from v2.src.services.google import GoogleIntegrationManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class SuperRAGSystem:
    def __init__(self):
        self.document_processor = EnhancedDocumentProcessor()
        self.conversation_manager = ConversationManager()
        self.web_search_manager = WebSearchManager()
        self.model_manager = ModelManager()
        self.google_manager = GoogleIntegrationManager()
        
        self.document_collection = None
        self.setup_complete = False
        self.session_start = datetime.now()
        
    def setup_system(self, clear_existing: bool = False):
        """Initialize the complete enhanced RAG system"""
        print("📊 Setting up super enhanced RAG system...")
        
        try:
            # Setup vector database
            self.document_collection = self.document_processor.setup_document_processing("super_documents")
            
            # Process documents
            success = self.document_processor.process_local_documents(
                self.document_collection, 
                folder_path="./documents",
                clear_existing=clear_existing
            )
            
            if success:
                stats = self.document_processor.get_collection_stats(self.document_collection)
                print(f"📈 Collection stats: {stats.get('total_documents', 0)} documents")
            
            self.setup_complete = True
            print("✅ Super enhanced RAG system ready!")
            
        except Exception as e:
            print(f"❌ System setup failed: {e}")
            sys.exit(1)
    
    def analyze_query_enhanced(self, question: str) -> dict:
        """Super enhanced query analysis with Google detection"""
        question_lower = question.lower()
        
        analysis = {
            'needs_docs': any(keyword in question_lower for keyword in 
                            ['my', 'document', 'file', 'note', 'search', 'find in']),
            'needs_web': any(keyword in question_lower for keyword in 
                           ['latest', 'current', 'today', 'weather', 'news', 'recent', '2024', '2025']),
            'needs_google': any(keyword in question_lower for keyword in 
                              ['google drive', 'gmail', 'email', 'my drive', 'google doc', 'google docs']),
            'is_technical': any(term in question_lower for term in 
                              ['python', 'mysql', 'function', 'class', 'select', 'join', 'database']),
            'is_code_request': any(keyword in question_lower for keyword in 
                                 ['code', 'example', 'syntax', 'how to', 'implement']),
            'is_explanation': any(keyword in question_lower for keyword in 
                                ['explain', 'what is', 'how does', 'why']),
            'word_count': len(question_lower.split()),
            'urgency': 'high' if any(word in question_lower for word in ['urgent', 'asap', 'quick']) else 'normal'
        }
        
        return analysis
    
    def handle_query_enhanced(self, question: str) -> str:
        """Enhanced query handler with all features including Google integration"""
        if not self.setup_complete:
            return "❌ System not ready. Please wait for setup."
        
        # Handle special commands
        if self.handle_special_commands(question):
            return ""
        
        start_time = time.time()
        analysis = self.analyze_query_enhanced(question)
        
        print(f"🔍 Query analysis: {analysis}")
        
        # Determine response strategy
        response = ""
        query_type = "general"
        
        if analysis['needs_google'] and self.google_manager.is_authenticated:
            # Google Drive/Gmail search
            google_results = self.search_google_sources(question)
            response = self.generate_smart_response(question, google_results, "google")
            query_type = "google_search"
        
        elif analysis['needs_docs']:
            # Document search
            context = self.search_documents_enhanced(question)
            if context:
                response = self.generate_smart_response(question, context, "documents")
                query_type = "document_search"
            else:
                response = "I couldn't find relevant information in your documents. " + \
                          self.generate_smart_response(question, "", "general")
                query_type = "document_search_empty"
        
        elif analysis['needs_web']:
            # Web search
            web_results = self.web_search_manager.search_web(question)
            response = self.generate_smart_response(question, web_results, "web")
            query_type = "web_search"
        
        elif analysis['is_code_request']:
            # Code-focused response
            response = self.generate_smart_response(question, "", "code")
            query_type = "code_request"
        
        else:
            # General knowledge
            response = self.generate_smart_response(question, "", "general")
            query_type = "general_knowledge"
        
        return response
    
    def search_google_sources(self, query: str) -> str:
        """Search Google Drive and Gmail"""
        print("🔍 Searching Google Workspace...")
        
        drive_results = self.google_manager.search_google_drive(query)
        gmail_results = self.google_manager.search_gmail(query)
        
        all_results = drive_results + gmail_results
        
        if not all_results:
            return "No relevant information found in your Google Workspace."
        
        # Format results
        context_parts = ["I found relevant information in your Google Workspace:"]
        
        for i, result in enumerate(all_results[:5], 1):
            source = result.get('source', 'unknown')
            source_icon = "📧" if source == 'gmail' else "📁"
            context_parts.append(f"\n{source_icon} Result {i} from {source}:")
            
            if source == 'gmail':
                context_parts.append(f"📨 Subject: {result.get('subject', 'No subject')}")
                context_parts.append(f"👤 From: {result.get('from', 'Unknown')}")
                context_parts.append(f"📅 Date: {result.get('date', 'Unknown')}")
                context_parts.append(f"📝 Snippet: {result.get('content', '')}")
            else:
                context_parts.append(f"📄 File: {result.get('file_name', 'Unknown')}")
                context_parts.append(f"📊 Type: {result.get('file_type', 'Unknown')}")
        
        return "\n".join(context_parts)
    
    def search_documents_enhanced(self, query: str, max_results: int = 5) -> str:
        """Enhanced document search with smart filtering"""
        print("📚 Searching your documents with smart filtering...")
        
        results = self.document_processor.search_local_documents(
            self.document_collection, 
            query, 
            max_results=max_results,
            include_metadata=True
        )
        
        if not results:
            return ""
        
        # Smart filtering: only include high-quality results
        high_quality_results = [r for r in results if r['similarity_score'] > 0.3]
        
        if not high_quality_results:
            return ""
        
        # Format context
        context_parts = ["I found highly relevant information in your documents:"]
        
        for i, result in enumerate(high_quality_results[:3], 1):  # Limit to top 3
            context_parts.append(f"\n🎯 Result {i} (Score: {result['similarity_score']:.3f})")
            context_parts.append(f"📄 Source: {result.get('file_name', 'Unknown')}")
            context_parts.append(f"📝 Content: {result['content']}")
        
        return "\n".join(context_parts)
    
    def generate_smart_response(self, question: str, context: str, response_type: str) -> str:
        """Generate smart responses based on type"""
        history = self.conversation_manager.get_conversation_history()
        
        prompts = {
            "google": f"Context from Google:\n{context}\n\nQuestion: {question}\n\nAnswer:",
            "documents": f"Context from Documents:\n{context}\n\nQuestion: {question}\n\nAnswer:",
            "web": f"Context from Web:\n{context}\n\nQuestion: {question}\n\nAnswer:",
            "code": f"Question: {question}\n\nProvide code example:",
            "general": f"Question: {question}\n\nAnswer:"
        }
        
        prompt = prompts.get(response_type, prompts["general"])
        
        try:
            response = self.model_manager.invoke_model(prompt)
            self.conversation_manager.add_conversation(question, response)
            return response
        except Exception as e:
            return f"Response generation error: {e}"
    
    def handle_special_commands(self, user_input: str) -> bool:
        """Handle enhanced special commands"""
        input_lower = user_input.lower().strip()
        
        command_handlers = {
            '/help': self.show_enhanced_help,
            '/models': self.show_models,
            '/switch': lambda: self.switch_model(user_input),
            '/clear': lambda: self.conversation_manager.clear_memory() or print("🧹 Conversation memory cleared!"),
            '/reload': lambda: self.setup_system(clear_existing=True) or print("🔄 Documents reloaded!"),
            '/history': lambda: print(f"\n📜 Conversation History:\n{self.conversation_manager.get_conversation_history()}"),
            '/web': lambda: print(f"🌐 Web search: {'✅ Available' if self.web_search_manager.search_tool else '❌ Unavailable'}"),
            '/google': self.show_google_status,
            '/quit': lambda: sys.exit(0)
        }
        
        for command, handler in command_handlers.items():
            if input_lower == command or (command == '/switch' and input_lower.startswith('/switch ')):
                handler()
                return True
        
        return False

    def show_enhanced_help(self):
        print("""
        Commands:
        /help - Show this help
        /models - List models
        /switch <model> - Switch model
        /clear - Clear memory
        /reload - Reload docs
        /history - Show history
        /web - Web search status
        /google - Google status
        /quit - Exit
        """)

    def show_models(self):
        models = self.model_manager.get_available_models()
        print(f"Available models: {list(models.keys())}")

    def switch_model(self, command):
        try:
            model = command.split()[1]
            self.model_manager.setup_model(model)
        except:
            print("Usage: /switch <model_name>")

    def show_google_status(self):
        status = self.google_manager.get_google_status()
        print(f"Google Status: {status}")
