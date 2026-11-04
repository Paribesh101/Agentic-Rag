# v2/src/core/memory.py
import json
import os
from datetime import datetime
from typing import List, Dict

class ConversationManager:
    def __init__(self, history_file: str = "conversation_history.json"):
        self.history_file = history_file
        self.history = self._load_history()
        
    def _load_history(self) -> List[Dict[str, str]]:
        """Load conversation history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading history: {e}")
                return []
        return []
    
    def _save_history(self):
        """Save conversation history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving history: {e}")
            
    def add_conversation(self, question: str, response: str):
        """Add a new exchange to history"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "response": response
        }
        self.history.append(entry)
        self._save_history()
        
    def get_conversation_history(self, limit: int = 5) -> str:
        """Get formatted conversation history for context"""
        if not self.history:
            return "No previous conversation."
            
        recent = self.history[-limit:]
        formatted = []
        
        for entry in recent:
            formatted.append(f"User: {entry['question']}")
            formatted.append(f"Assistant: {entry['response']}")
            
        return "\n".join(formatted)
    
    def clear_memory(self):
        """Clear conversation history"""
        self.history = []
        if os.path.exists(self.history_file):
            os.remove(self.history_file)
        print("🧹 Conversation memory cleared")
