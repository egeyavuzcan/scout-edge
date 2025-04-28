"""
Serper tool - Tool for fetching Google search results for the Scout-Edge platform.
"""
import logging
import sys
import os
import json
import requests
from typing import Dict, List, Any, Optional

from langchain.tools import BaseTool

# Import configuration settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


class SerperSearchTool(BaseTool):
    """
    LangChain tool using Serper.dev API to fetch Google search results.
    """
    name = "serper_search"
    description = "Used to fetch search results from Google. Ideal for searching AI and technology news."
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the SerperSearchTool class.
        
        Args:
            api_key (str, optional): Serper API key
        """
        super().__init__()
        self.api_key = api_key or config.SERPER_API_KEY
        self.base_url = "https://google.serper.dev/search"
        
    def _run(self, query: str, search_type: str = "news", 
             num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch Google search results based on specified query and parameters.
        
        Args:
            query (str): Search query
            search_type (str): Search type (news, web, places, images)
            num_results (int): Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results
        """
        if not self.api_key:
            error_msg = "Serper API key not found. Please define SERPER_API_KEY in config.py."
            logger.error(error_msg)
            return {"error": error_msg}
            
        try:
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "gl": "us",  # Location setting (USA)
                "hl": "en",  # Language setting (English)
                "num": num_results
            }
            
            response = requests.post(
                self.base_url, 
                headers=headers, 
                json=payload
            )
            
            if response.status_code != 200:
                error_msg = f"Serper API error: {response.status_code}, {response.text}"
                logger.error(error_msg)
                return {"error": error_msg}
                
            data = response.json()
            results = []
            
            # Process results according to search type
            if search_type == "news" and "news" in data:
                for item in data["news"]:
                    result = {
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "date": item.get("date", ""),
                        "source": item.get("source", ""),
                        "imageUrl": item.get("imageUrl", ""),
                        "type": "news"
                    }
                    results.append(result)
            elif "organic" in data:
                for item in data["organic"]:
                    result = {
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "position": item.get("position", 0),
                        "type": "web"
                    }
                    results.append(result)
            
            logger.info(f"Found {len(results)} results in Google search.")
            return results
            
        except Exception as e:
            error_msg = f"Error during Serper search: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    async def _arun(self, query: str, search_type: str = "news", 
                   num_results: int = 10) -> List[Dict[str, Any]]:
        """Async method required for the tool (currently calls the sync method)"""
        return self._run(query, search_type, num_results)


class NewsAnalyzer:
    """
    Class for analyzing news results.
    """
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the NewsAnalyzer class.
        
        Args:
            api_key (str, optional): Serper API key
        """
        self.serper_tool = SerperSearchTool(api_key=api_key)
        
    def search_ai_news(self, query: str = "artificial intelligence", 
                      num_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for AI-related news.
        
        Args:
            query (str): Search query
            num_results (int): Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results
        """
        # Search for AI-related news
        full_query = f"{query} latest news research developments"
        
        results = self.serper_tool._run(
            query=full_query,
            search_type="news",
            num_results=num_results
        )
        
        return results if isinstance(results, list) else []
        
    def analyze_news_trends(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze trends from news items.
        
        Args:
            news_items (List[Dict[str, Any]]): News items to analyze
            
        Returns:
            Dict[str, Any]: Trend analysis results
        """
        if not news_items:
            return {"error": "No news found for analysis."}
            
        # Source analysis
        source_counts = {}
        for item in news_items:
            source = item.get("source", "")
            if source:
                source_counts[source] = source_counts.get(source, 0) + 1
                
        # Date analysis
        date_counts = {}
        for item in news_items:
            date = item.get("date", "")
            if date:
                date_counts[date] = date_counts.get(date, 0) + 1
        
        # Create trend report
        trends = {
            "total_news": len(news_items),
            "top_sources": sorted(source_counts.items(), 
                                 key=lambda x: x[1], reverse=True)[:10],
            "publication_dates": sorted(date_counts.items()),
            "latest_news": sorted(news_items, 
                               key=lambda x: x.get("date", ""), 
                               reverse=True)[:5]
        }
        
        return trends
