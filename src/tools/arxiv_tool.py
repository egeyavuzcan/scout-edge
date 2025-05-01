import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import arxiv
from langchain.tools import BaseTool

import config

logger = logging.getLogger(__name__)


class ArxivSearchTool(BaseTool):
    """Tool for searching scientific papers on ArXiv."""
    name: str = "arxiv_search"
    description: str = (
        "Search ArXiv for research papers based on a query. "
        "Useful for finding recent scientific literature."
    )
    arxiv_client: Optional[arxiv.Client] = None

    def __init__(self, **kwargs):
        """Initialize the ArxivSearchTool."""
        super().__init__(**kwargs)
        try:
            self.arxiv_client = arxiv.Client()
            logger.info("ArXiv client initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing ArXiv client: {e}")
            self.arxiv_client = None

    def _run(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for papers on ArXiv based on the query.

        Args:
            query: The search query string.

        Returns:
            A list of dictionaries, each containing details of a paper.
        """
        if not self.arxiv_client:
            return [{"error": "ArXiv client not initialized."}]

        max_results = config.ARXIV_MAX_RESULTS
        sort_by = arxiv.SortCriterion.SubmittedDate
        sort_order = arxiv.SortOrder.Descending

        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=sort_by,
                sort_order=sort_order
            )

            results = []
            logger.info(f"Executing ArXiv search for query: '{query}'")
            papers = list(self.arxiv_client.results(search))

            if not papers:
                logger.info(f"No ArXiv papers found for query: '{query}'")
                return [{"message": "No results found."}]

            for result in papers:
                authors = [author.name for author in result.authors]

                paper_details = {
                    "entry_id": result.entry_id,
                    "title": result.title,
                    "authors": authors,
                    "published_date": result.published.strftime("%Y-%m-%d"),
                    "summary": result.summary,
                    "pdf_url": result.pdf_url,
                    "doi": result.doi,
                    "primary_category": result.primary_category,
                    "categories": result.categories,
                    "source": "arxiv"
                }
                results.append(paper_details)

            logger.info(f"Found {len(results)} papers from ArXiv for query: '{query}'")
            return results

        except Exception as e:
            logger.error(f"Error during ArXiv search for query '{query}': {e}")
            return [{"error": f"An error occurred during ArXiv search: {e}"}]

    async def _arun(self, query: str) -> List[Dict[str, Any]]:
        """Asynchronous version of the search logic."""
        logger.info("Async search request, running sync version.")
        return self._run(query)


class ArxivTrendAnalyzer:
    """
    Analyzes trends based on ArXiv papers.
    """

    def __init__(self, tags: List[str], arxiv_tool: ArxivSearchTool):
        """Initialize the ArxivTrendAnalyzer."""
        self.tags = tags
        self.arxiv_tool = arxiv_tool
        logger.info(f"ArxivTrendAnalyzer initialized with tags: {tags}")

    def collect_data(
        self,
        days: int = 7,
        max_papers: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Collect data from ArXiv for the specified tags and time period.

        Args:
            days (int): The number of past days to consider for trends.
            max_papers (int): Max papers to fetch per tag.

        Returns:
            List[Dict[str, Any]]: A list of paper data.
        """
        all_papers = []
        if not self.tags:
            logger.warning("No tags provided for data collection.")
            return []

        papers_per_tag = max_papers // len(self.tags)

        cutoff_date = datetime.now() - timedelta(days=days)

        for tag in self.tags:
            papers = self.arxiv_tool._run(query=tag)

            if isinstance(papers, list) and papers and "error" not in papers[0]:
                recent_papers = [
                    p for p in papers
                    if datetime.strptime(p['published_date'], "%Y-%m-%d")
                    >= cutoff_date
                ]
                all_papers.extend(recent_papers[:papers_per_tag])
            elif isinstance(papers, list) and papers and "message" in papers[0]:
                logger.info(f"No results for tag '{tag}' on ArXiv.")
            elif isinstance(papers, list) and papers and "error" in papers[0]:
                logger.warning(
                    f"Error fetching data for tag '{tag}': {papers[0]['error']}"
                )

        logger.info(f"Collected {len(all_papers)} recent papers in total.")
        return all_papers

    def analyze(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the collected paper data to identify trends.

        Args:
            papers (List[Dict[str, Any]]): List of paper data.

        Returns:
            Dict[str, Any]: Analysis results including top papers and categories.
        """
        if not papers:
            return {"error": "No paper data to analyze."}

        category_counts = {}
        for paper in papers:
            cat = paper.get("primary_category")
            if cat:
                category_counts[cat] = category_counts.get(cat, 0) + 1

        sorted_papers = sorted(
            papers, key=lambda x: x.get("published_date", ""), reverse=True
        )

        top_n = 5
        top_papers = sorted_papers[:top_n]

        analysis_summary = {
            "total_papers_analyzed": len(papers),
            "top_papers": [
                {
                    "title": p.get("title"),
                    "url": p.get("pdf_url", p.get("entry_id")),
                    "published": p.get("published_date")
                } for p in top_papers
            ],
            "category_distribution": sorted(
                category_counts.items(),
                key=lambda item: item[1],
                reverse=True
            )[:10],
            "comment": "Trend analysis based on recent paper categories and publication dates."
        }

        return analysis_summary
