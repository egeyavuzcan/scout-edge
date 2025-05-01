"""
Serper tool - Tool for fetching Google search results for the Scout-Edge platform.
"""
import logging
from typing import Optional, Type, Any, List, Dict

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

# Import configuration settings
import config

logger = logging.getLogger(__name__)


class SerperSearchInput(BaseModel):
    """Input schema for SerperSearchTool."""
    query: str = Field(description="The search query for Serper API")


class SerperSearchTool(BaseTool):
    """Tool for performing searches using the Serper API."""
    name: str = "serper_search"
    description: str = (
        "Uses Google Serper API to search the web for a given query. "
        "Useful for finding real-time information or news."
    )
    args_schema: Type[BaseModel] = SerperSearchInput
    api_key: Optional[str] = None  # Define at class level
    search_wrapper: Optional[Any] = None  # Define at class level
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the SerperSearchTool class.
        
        Args:
            api_key (str, optional): Serper API key
        """
        super().__init__()
        self.api_key = api_key or config.SERPER_API_KEY
        
    def _run(self, query: str) -> str:
        """Run the search query through the Serper API."""
        if not self.search_wrapper:
            logger.error("Serper search wrapper not initialized. API key might be missing.")
            return "Error: Serper API key not configured or wrapper failed to initialize."
        try:
            logger.info(f"Performing Serper search for query: '{query}'")
            # Use the initialized wrapper to run the search
            results = self.search_wrapper.run(query)
            logger.info("Serper search completed.")
            return results
        except Exception as e:
            logger.error(f"Error during Serper search: {e}")
            return f"Error performing search: {e}"

    async def _arun(self, query: str) -> str:
        """Async method required for the tool (currently calls the sync method)"""
        return self._run(query)


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
            query=full_query
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
