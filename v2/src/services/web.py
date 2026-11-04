# v2/src/services/web.py
from typing import List, Dict
try:
    from duckduckgo_search import DDGS
    HAS_DDG = True
except ImportError:
    HAS_DDG = False

class WebSearchManager:
    def __init__(self):
        self.search_tool = HAS_DDG
        if not HAS_DDG:
            print("⚠️ duckduckgo-search not installed. Web search disabled.")
            
    def search_web(self, query: str, max_results: int = 5) -> str:
        """Perform web search and return formatted results"""
        if not self.search_tool:
            return "Web search is unavailable."
            
        print(f"🌐 Searching web for: {query}")
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append(r)
            
            if not results:
                return "No web results found."
                
            formatted = ["Web Search Results:"]
            for i, res in enumerate(results, 1):
                formatted.append(f"\nResult {i}:")
                formatted.append(f"Title: {res.get('title', 'No title')}")
                formatted.append(f"URL: {res.get('href', 'No URL')}")
                formatted.append(f"Snippet: {res.get('body', 'No content')}")
                
            return "\n".join(formatted)
            
        except Exception as e:
            print(f"❌ Web search error: {e}")
            return f"Error performing web search: {e}"
