"""
GitHub tool - Search and process GitHub repositories for the Scout-Edge platform.
"""
import logging
import sys
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from github import Github, GithubException
from langchain.tools import BaseTool

# Import configuration settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


class GitHubTrendTool(BaseTool):
    """
    LangChain tool for searching AI projects from GitHub.
    """
    name = "github_trend_search"
    description = "Used to search for artificial intelligence projects on GitHub and analyze trends."
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the GitHubTrendTool class.
        
        Args:
            api_key (str, optional): GitHub API key
        """
        super().__init__()
        self.api_key = api_key or config.GITHUB_API_KEY
        self.github = Github(self.api_key)
        
    def _run(self, query: str, min_stars: int = 100, max_results: int = 10, 
             time_period_days: int = 30, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for projects from GitHub based on specified query and parameters.
        
        Args:
            query (str): Search query
            min_stars (int): Minimum number of stars
            max_results (int): Maximum number of results
            time_period_days (int): How many days of projects to search
            language (str, optional): Programming language filter
            
        Returns:
            List[Dict[str, Any]]: List of found projects
        """
        # Calculate recent date
        if time_period_days > 0:
            cutoff_date = datetime.now() - timedelta(days=time_period_days)
            date_filter = f" created:>{cutoff_date.strftime('%Y-%m-%d')}"
        else:
            date_filter = ""
            
        # Language filter
        lang_filter = f" language:{language}" if language else ""
        
        # Star filter
        star_filter = f" stars:>{min_stars}"
        
        # Create the full query
        full_query = f"{query}{star_filter}{lang_filter}{date_filter}"
        
        try:
            # Perform GitHub search
            repositories = self.github.search_repositories(
                query=full_query,
                sort="stars",
                order="desc"
            )
            
            # Collect results
            results = []
            count = 0
            
            for repo in repositories:
                if count >= max_results:
                    break
                    
                # Extract repository information
                repo_dict = {
                    "id": repo.id,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "language": repo.language,
                    "created_at": repo.created_at.strftime("%Y-%m-%d"),
                    "updated_at": repo.updated_at.strftime("%Y-%m-%d"),
                    "url": repo.html_url,
                    "topics": repo.get_topics(),
                    "source": "github"
                }
                
                results.append(repo_dict)
                count += 1
                
                # To avoid exceeding API rate limits
                if count % 10 == 0:
                    time.sleep(2)
            
            logger.info(f"Found {len(results)} repositories from GitHub.")
            return results
            
        except GithubException as e:
            error_msg = f"Error during GitHub search: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    async def _arun(self, query: str, min_stars: int = 100, max_results: int = 10,
                  time_period_days: int = 30, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """Async method required for the tool (currently calls the sync method)"""
        return self._run(query, min_stars, max_results, time_period_days, language)


class GitHubTrendAnalyzer:
    """
    Class for analyzing trends from GitHub projects.
    """
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the GitHubTrendAnalyzer class.
        
        Args:
            api_key (str, optional): GitHub API key
        """
        self.api_key = api_key or config.GITHUB_API_KEY
        self.github_tool = GitHubTrendTool(api_key=self.api_key)
        self.tags = config.GITHUB_TAGS
        
    def get_trending_repos(self, days: int = 30, min_stars: int = 100, 
                           max_repos: int = 50) -> List[Dict[str, Any]]:
        """
        Get trending repositories from recent days.
        
        Args:
            days (int): How many days of projects to retrieve
            min_stars (int): Minimum number of stars
            max_repos (int): Maximum number of repositories
            
        Returns:
            List[Dict[str, Any]]: List of repositories
        """
        # Query based on tags
        all_repos = []
        
        for tag in self.tags:
            # Search separately for each tag
            repos = self.github_tool._run(
                query=tag,
                min_stars=min_stars,
                max_results=max_repos // len(self.tags),
                time_period_days=days
            )
            
            if isinstance(repos, list):
                all_repos.extend(repos)
            
            # Brief wait to avoid exceeding API rate limits
            time.sleep(3)
            
        return all_repos
        
    def analyze_trends(self, repos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze repositories to determine trends.
        
        Args:
            repos (List[Dict[str, Any]]): Repositories to analyze
            
        Returns:
            Dict[str, Any]: Trend analysis results
        """
        if not repos:
            return {"error": "No repositories found for analysis."}
            
        # Language analysis
        language_counts = {}
        for repo in repos:
            language = repo.get("language")
            if language:
                language_counts[language] = language_counts.get(language, 0) + 1
                
        # Topic analysis
        topic_counts = {}
        for repo in repos:
            for topic in repo.get("topics", []):
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
                
        # Calculate score for repos (based on stars, forks, and recency)
        for repo in repos:
            stars = repo.get("stars", 0)
            forks = repo.get("forks", 0)
            
            # Recency score (newer updates get a higher score)
            updated_date = datetime.strptime(repo.get("updated_at", "2000-01-01"), "%Y-%m-%d")
            days_since_update = (datetime.now() - updated_date).days
            recency_score = max(1, 30 - days_since_update) / 30  # Between 0-1
            
            # Total score
            trend_score = (stars * 0.6) + (forks * 0.3) + (recency_score * 100)
            repo["trend_score"] = trend_score
        
        # Sort trending repos by score
        trending_repos = sorted(repos, key=lambda x: x.get("trend_score", 0), reverse=True)
        
        # Create trend report
        trends = {
            "total_repos": len(repos),
            "top_languages": sorted(language_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "top_topics": sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:15],
            "top_trending_repos": trending_repos[:10]
        }
        
        return trends
