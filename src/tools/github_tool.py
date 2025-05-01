import logging
from typing import Dict, Any, Optional, List, Type

import requests
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

# Import configuration settings
import config

logger = logging.getLogger(__name__)


class GitHubTrendInput(BaseModel):
    """Input schema for GitHubTrendTool."""
    query: str = Field(description="The search query for GitHub repositories")


class GitHubTrendTool(BaseTool):
    """Tool for searching trending AI projects on GitHub."""
    name: str = "github_trend_search"
    description: str = (
        "Searches GitHub for trending repositories based on a query, "
        "focusing on stars and recent activity. Useful for finding popular "
        "AI projects."
    )
    args_schema: Type[BaseModel] = GitHubTrendInput
    github_api_key: Optional[str] = None

    def __init__(self, **kwargs: Any):
        """Initialize the GitHubTrendTool."""
        super().__init__(**kwargs)
        self.github_api_key = config.GITHUB_API_KEY
        if not self.github_api_key:
            logger.warning(
                "GitHub API key not found. Requests will be unauthenticated."
            )

    def _run(self, query: str) -> List[Dict[str, Any]]:
        """
        Search GitHub for trending repositories matching the query.

        Args:
            query: The search query string (e.g., 'artificial intelligence').

        Returns:
            A list of dictionaries, each containing details of a trending repo.
        """
        # Default internal parameters for the search
        sort = "stars"  # Focus on popular repositories
        order = "desc"
        per_page = config.GITHUB_MAX_RESULTS  # Limit results via config

        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.github_api_key:
            headers["Authorization"] = f"token {self.github_api_key}"

        # Construct the search URL
        # Example: Find repositories matching 'query', sort by stars desc
        search_url = (
            f"https://api.github.com/search/repositories?q={query}"
            f"&sort={sort}&order={order}&per_page={per_page}"
        )

        logger.info(f"Executing GitHub search: {search_url}")

        try:
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()  # Raise HTTPError for bad responses (4XX, 5XX)

            data = response.json()
            items = data.get("items", [])

            if not items:
                logger.info(f"No GitHub repositories found for query: '{query}'")
                return [{"message": "No results found."}]

            results = []
            for item in items:
                repo_details = {
                    "name": item.get("name"),
                    "full_name": item.get("full_name"),
                    "url": item.get("html_url"),
                    "description": item.get("description"),
                    "stars": item.get("stargazers_count"),
                    "forks": item.get("forks_count"),
                    "language": item.get("language"),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                    "owner": item.get("owner", {}).get("login"),
                    "source": "github"
                }
                results.append(repo_details)

            logger.info(
                f"Found {len(results)} trending repositories on GitHub for query: '{query}'"
            )
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Error during GitHub search for query '{query}': {e}")
            return [{"error": f"An error occurred during GitHub search: {e}"}]
        except Exception as e:
            logger.error(
                f"Unexpected error processing GitHub results for query '{query}': {e}"
            )
            return [{"error": f"An unexpected error occurred: {e}"}]

    async def _arun(self, query: str) -> List[Dict[str, Any]]:
        """Asynchronous version of the search logic."""
        # Placeholder: True async would use an async HTTP client like httpx
        logger.info("Async GitHub search request, running sync version.")
        return self._run(query)


class GitHubTrendAnalyzer:
    """
    Analyzes trends based on GitHub repositories.
    """

    def __init__(self, tags: List[str], github_tool: GitHubTrendTool):
        """Initialize the GitHubTrendAnalyzer."""
        self.tags = tags
        self.github_tool = github_tool
        logger.info(f"GitHubTrendAnalyzer initialized with tags: {tags}")

    def collect_data(
        self,
        days: int = 30,
        max_repos: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Collect data from GitHub for the specified tags and time period.

        Args:
            days (int): The number of past days to consider for trends.
            max_repos (int): The maximum number of repositories to fetch per tag.

        Returns:
            List[Dict[str, Any]]: A list of repository data.
        """
        all_repos = []
        repos_per_tag = max_repos // len(self.tags) if self.tags else max_repos

        for tag in self.tags:
            # Search separately for each tag
            # Note: The underlying _run now handles default params like max_results
            # We might need a way to pass max_repos if finer control is needed later.
            repos = self.github_tool._run(query=tag)

            if isinstance(repos, list) and repos and "error" not in repos[0]:
                # Limit results per tag if needed (though _run already limits)
                all_repos.extend(repos[:repos_per_tag])
            elif isinstance(repos, list) and repos and "message" in repos[0]:
                logger.info(f"No results for tag '{tag}' on GitHub.")
            elif isinstance(repos, list) and repos and "error" in repos[0]:
                logger.warning(
                    f"Error fetching data for tag '{tag}': {repos[0]['error']}"
                )

        logger.info(f"Collected {len(all_repos)} repositories in total.")
        return all_repos

    def analyze(self, repos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the collected repository data to identify trends.

        Args:
            repos (List[Dict[str, Any]]): List of repository data.

        Returns:
            Dict[str, Any]: Analysis results including top repositories and scores.
        """
        if not repos:
            return {"error": "No repository data to analyze."}

        # Calculate scores for each repository
        scored_repos = []
        for repo in repos:
            score = self._calculate_score(repo)
            scored_repos.append({**repo, "score": score})

        # Sort repositories by score (descending)
        sorted_repos = sorted(
            scored_repos, key=lambda x: x.get("score", 0), reverse=True
        )

        # Basic analysis: top N repositories, language distribution
        top_n = 5
        top_repositories = sorted_repos[:top_n]

        language_counts = {}
        for repo in repos:
            lang = repo.get("language")
            if lang:
                language_counts[lang] = language_counts.get(lang, 0) + 1

        analysis_summary = {
            "total_repositories_analyzed": len(repos),
            "top_repositories": [
                {
                    "name": r.get("full_name"),
                    "url": r.get("url"),
                    "score": r.get("score")
                } for r in top_repositories
            ],
            "language_distribution": language_counts,
            "comment": "Trend analysis based on repository scores (stars, forks, recency)."
        }

        return analysis_summary

    def _calculate_score(self, repo: Dict[str, Any]) -> float:
        """Calculate a score for a repository based on stars, forks, recency."""
        stars = repo.get("stars", 0)
        forks = repo.get("forks", 0)

        # Recency score (newer updates get a higher score)
        try:
            updated_at_str = repo.get("updated_at", "2000-01-01T00:00:00Z")
            # Handle potential Z suffix for UTC timezone
            if updated_at_str.endswith('Z'):
                updated_at_str = updated_at_str[:-1] + '+00:00'
            updated_date = datetime.fromisoformat(updated_at_str)
            # Ensure timezone awareness if comparing with timezone-aware datetime.now()
            # If updated_date is naive, make datetime.now() naive for comparison
            now = datetime.now(updated_date.tzinfo) if updated_date.tzinfo else datetime.now()
            days_since_update = (now - updated_date).days
        except (ValueError, TypeError):
            # Default to a large number of days if parsing fails
            days_since_update = 365 * 10

        recency_score = max(0, 30 - days_since_update) / 30  # Scale 0-1

        # Simple weighted score - adjust weights as needed
        score = (stars * 0.5) + (forks * 0.3) + (recency_score * 0.2 * 100)
        return round(score, 2)
