"""
ArXiv tool - Search and process ArXiv papers for the Scout-Edge platform.
"""
import logging
import sys
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import arxiv
from langchain.tools import BaseTool

# Import configuration settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


class ArxivSearchTool(BaseTool):
    """
    LangChain tool for searching AI papers from ArXiv.
    """
    name = "arxiv_search"
    description = "Used to search and analyze artificial intelligence papers from ArXiv."
    
    def _run(self, query: str, max_results: int = 10, time_period_days: int = 30,
             categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search for papers from ArXiv based on specified query and parameters.
        
        Args:
            query (str): Search query
            max_results (int): Maximum number of results
            time_period_days (int): How many days of papers to search
            categories (List[str], optional): Categories to search
            
        Returns:
            List[Dict[str, Any]]: List of found papers
        """
        if categories is None:
            categories = config.ARXIV_CATEGORIES
            
        # Combine categories in ArXiv format
        category_query = " OR ".join([f"cat:{cat}" for cat in categories])
        
        # Create the full query
        full_query = f"({category_query}) AND ({query})"
        
        try:
            # Configure ArXiv search
            search = arxiv.Search(
                query=full_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            # Collect results
            results = []
            for paper in search.results():
                # Check if within time_period_days
                if time_period_days > 0:
                    paper_date = paper.published
                    cutoff_date = datetime.now() - timedelta(days=time_period_days)
                    if paper_date < cutoff_date:
                        continue
                
                # Extract paper information
                authors = [author.name for author in paper.authors]
                categories = [cat for cat in paper.categories]
                
                # Create result dictionary
                paper_dict = {
                    "id": paper.entry_id,
                    "title": paper.title,
                    "authors": authors,
                    "summary": paper.summary,
                    "categories": categories,
                    "published": paper.published.strftime("%Y-%m-%d"),
                    "updated": paper.updated.strftime("%Y-%m-%d") if paper.updated else None,
                    "url": paper.pdf_url,
                    "source": "arxiv"
                }
                
                results.append(paper_dict)
            
            logger.info(f"Found {len(results)} papers from ArXiv.")
            return results
            
        except Exception as e:
            error_msg = f"Error during ArXiv search: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    async def _arun(self, query: str, max_results: int = 10, time_period_days: int = 30,
                   categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Async method required for the tool (currently calls the sync method)"""
        return self._run(query, max_results, time_period_days, categories)


class ArxivTrendAnalyzer:
    """
    Class for analyzing trends from ArXiv papers.
    """
    def __init__(self, categories: Optional[List[str]] = None):
        """
        Initialize the ArxivTrendAnalyzer class.
        
        Args:
            categories (List[str], optional): Categories to analyze
        """
        self.categories = categories or config.ARXIV_CATEGORIES
        self.arxiv_tool = ArxivSearchTool()
        
    def get_recent_papers(self, days: int = 7, 
                          max_papers: int = 100) -> List[Dict[str, Any]]:
        """
        Get papers from recent days.
        
        Args:
            days (int): How many days of papers to retrieve
            max_papers (int): Maximum number of papers
            
        Returns:
            List[Dict[str, Any]]: List of papers
        """
        # Query based on category
        all_papers = []
        
        for category in self.categories:
            # Search for each category separately
            papers = self.arxiv_tool._run(
                query=f"cat:{category}",
                max_results=max_papers // len(self.categories),
                time_period_days=days,
                categories=[category]
            )
            
            if isinstance(papers, list):
                all_papers.extend(papers)
            
            # Brief wait to avoid exceeding API rate limits
            time.sleep(1)
            
        return all_papers
        
    def analyze_trends(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze papers to determine trends.
        
        Args:
            papers (List[Dict[str, Any]]): Papers to analyze
            
        Returns:
            Dict[str, Any]: Trend analysis results
        """
        if not papers:
            return {"error": "No papers found for analysis."}
            
        # Simple trend analysis
        # This part could be enhanced with LLM in the future
        
        # Author analysis
        author_counts = {}
        for paper in papers:
            for author in paper.get("authors", []):
                author_counts[author] = author_counts.get(author, 0) + 1
                
        # Category analysis
        category_counts = {}
        for paper in papers:
            for category in paper.get("categories", []):
                category_counts[category] = category_counts.get(category, 0) + 1
                
        # Publication date analysis
        date_counts = {}
        for paper in papers:
            pub_date = paper.get("published")
            if pub_date:
                date_counts[pub_date] = date_counts.get(pub_date, 0) + 1
        
        # Create trend report
        trends = {
            "total_papers": len(papers),
            "top_authors": sorted(author_counts.items(), 
                                   key=lambda x: x[1], reverse=True)[:10],
            "top_categories": sorted(category_counts.items(), 
                                      key=lambda x: x[1], reverse=True),
            "publication_dates": sorted(date_counts.items()),
            "latest_papers": sorted(papers, 
                                     key=lambda x: x.get("published", ""), 
                                     reverse=True)[:5]
        }
        
        return trends
