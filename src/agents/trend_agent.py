"""
Main agent responsible for orchestrating data collection and analysis.
"""
import logging
import json
from typing import Dict, List, Any, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool

from ..tools.arxiv_tool import ArxivSearchTool
from ..tools.github_tool import GitHubTrendTool
from ..tools.serper_search_tool import SerperSearchTool
from ..tools.trend_analyzer_tool import TrendAnalyzerTool
from ..config import Config

logger = logging.getLogger(__name__)

class TrendAgent:
    """
    The core agent that manages tools and executes tasks for collecting and analyzing AI trends.

    Attributes:
        config (Config): Configuration object holding settings and API keys.
        llm (ChatOpenAI): The language model instance used by the agent and tools.
        tools (List[Tool]): A list of tools available to the agent (ArXiv, GitHub, Serper, Analyzer).
        agent_executor (AgentExecutor): The executor responsible for running the agent logic.
        default_queries (Dict[str, str]): Default search queries for different sources.
    """

    def __init__(self, config: Config):
        """
        Initializes the TrendAgent.

        Args:
            config (Config): The application configuration.

        Raises:
            ValueError: If essential configuration (like OpenAI API key) is missing.
        """
        self.config = config
        if not self.config.OPENAI_API_KEY:
            logger.error("OpenAI API key is missing. Cannot initialize TrendAgent.")
            raise ValueError("OpenAI API key not found in configuration.")

        logger.info(f"Initializing TrendAgent with LLM: {self.config.LLM_MODEL}")

        # Initialize LLM
        self.llm = ChatOpenAI(
            temperature=self.config.LLM_TEMPERATURE,
            model_name=self.config.LLM_MODEL,
            openai_api_key=self.config.OPENAI_API_KEY
        )

        # Initialize tools
        self.tools = self._initialize_tools()

        # Initialize Agent using Langchain Hub prompt
        # prompt = hub.pull("hwchase17/react") # Using a standard ReAct prompt
        # Using a custom or potentially modified prompt might be better
        prompt = self._get_react_prompt_template()

        agent = create_react_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.config.VERBOSE_MODE,
            handle_parsing_errors=True, # Gracefully handle potential output parsing errors
            max_iterations=5 # Limit iterations to prevent runaway loops
        )

        # Default queries (Consider making these configurable)
        self.default_queries = {
            'arxiv': 'artificial intelligence',
            'github': 'machine learning',
            'news': 'AI trends'
        }
        logger.info("TrendAgent initialized successfully.")

    def _initialize_tools(self) -> List[Tool]:
        """Initializes and returns the list of tools available to the agent."""
        tools = []
        logger.info("Initializing tools...")
        try:
            tools.append(ArxivSearchTool(max_results=self.config.ARXIV_MAX_RESULTS).tool())
            logger.debug("ArXivSearchTool initialized.")
        except Exception as e:
            logger.warning(f"Failed to initialize ArxivSearchTool: {e}")

        try:
            # Pass LLM to GitHub tool if needed for summarization or analysis within the tool itself
            tools.append(GitHubTrendTool(api_key=self.config.GITHUB_API_KEY, max_results=self.config.GITHUB_MAX_RESULTS).tool())
            logger.debug("GitHubTrendTool initialized.")
        except Exception as e:
            logger.warning(f"Failed to initialize GitHubTrendTool: {e}")

        try:
            if self.config.SERPER_API_KEY:
                tools.append(SerperSearchTool(api_key=self.config.SERPER_API_KEY).tool())
                logger.debug("SerperSearchTool initialized.")
            else:
                logger.warning("Serper API key not found. SerperSearchTool will not be available.")
        except Exception as e:
            logger.warning(f"Failed to initialize SerperSearchTool: {e}")

        try:
            # Pass the LLM instance to the analyzer tool
            tools.append(TrendAnalyzerTool(llm=self.llm).tool())
            logger.debug("TrendAnalyzerTool initialized.")
        except Exception as e:
            logger.warning(f"Failed to initialize TrendAnalyzerTool: {e}")

        if not tools:
             logger.warning("No tools were successfully initialized for the TrendAgent!")
        else:
             logger.info(f"Initialized {len(tools)} tools.")
        return tools

    def _get_react_prompt_template(self) -> PromptTemplate:
        """
        Defines the ReAct prompt template for the agent.
        This template guides the LLM on how to use the tools and reason.
        """
        template = """
        Answer the following questions as best you can. You have access to the following tools:

        {tools}

        Use the following format:

        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question

        When collecting data (like from ArXiv, GitHub, or News), gather the information first.
        When asked to analyze trends, use the 'TrendAnalyzerTool'. Provide the collected data to this tool as a JSON string dictionary, for example: 
        Action Input: {{"arxiv_data": [list_of_arxiv_results], "github_data": [list_of_github_results], "news_data": [list_of_news_results]}}
        Ensure the data passed to TrendAnalyzerTool is comprehensive if available.

        Begin!

        Question: {input}
        Thought:{agent_scratchpad}
        """
        return PromptTemplate.from_template(template)


    def run(self, query: str) -> Dict[str, Any]:
        """
        Runs the agent with a given query.
        This method is intended for general queries that might require the agent
        to decide which tool(s) to use.

        Args:
            query (str): The user's query.

        Returns:
            Dict[str, Any]: The result from the agent executor, typically containing the 'output'.
        """
        logger.info(f"Running agent with query: {query}")
        try:
            # Make sure tools are available
            if not self.agent_executor.tools:
                logger.error("Agent has no tools available to run the query.")
                return {"error": "Agent configuration error: No tools available."}
                
            result = self.agent_executor.invoke({"input": query})
            logger.info(f"Agent execution finished. Result keys: {result.keys()}")
            return result
        except Exception as e:
            logger.error(f"Error during agent execution: {e}", exc_info=True)
            # Provide a more user-friendly error message
            error_message = f"An error occurred while processing your request: {e}. Please check the logs for details."
            if "rate limit" in str(e).lower():
                error_message = "The request failed due to API rate limits. Please check your API plan or try again later."
            elif "api key" in str(e).lower():
                 error_message = "An API key error occurred. Please ensure your API keys in the .env file are correct and active."
            return {"error": error_message}

    def collect_trend_data(
        self,
        arxiv_query: Optional[str] = None,
        github_query: Optional[str] = None,
        news_query: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Collects trend data from specified sources using dedicated tools directly.

        Args:
            arxiv_query (Optional[str]): Query for ArXiv search.
            github_query (Optional[str]): Query for GitHub search.
            news_query (Optional[str]): Query for news search.
            max_results (Optional[int]): Maximum number of results per source.
                                         Defaults to config setting if not provided.

        Returns:
            Dict[str, Any]: A dictionary containing lists of results for each source,
                            e.g., {'arxiv_papers': [...], 'github_repos': [...], 'news_articles': [...]}.
                            Includes an 'error' key if any tool fails.
        """
        results: Dict[str, Any] = {
            'arxiv_papers': [],
            'github_repos': [],
            'news_articles': [],
            'errors': [] # Collect errors from individual tools
        }
        
        # Use default max_results if not provided
        max_res = max_results if max_results is not None else self.config.ARXIV_MAX_RESULTS
        
        logger.info(f"Starting data collection. Max results per source: {max_res}")

        # Find tools by name
        arxiv_tool = next((t for t in self.tools if t.name == 'arxiv_search'), None)
        github_tool = next((t for t in self.tools if t.name == 'github_trends'), None)
        news_tool = next((t for t in self.tools if t.name == 'serper_search'), None)

        # Run ArXiv Search
        if arxiv_query and arxiv_tool:
            try:
                logger.info(f"Running ArXiv search with query: '{arxiv_query}'")
                # Tool might return a string, attempt to parse if it looks like JSON list
                arxiv_result_str = arxiv_tool.run(f"{{"query": "{arxiv_query}", "max_results": {max_res}}}")
                try:
                    results['arxiv_papers'] = json.loads(arxiv_result_str)
                except json.JSONDecodeError:
                     logger.warning(f"ArXiv tool returned non-JSON string: {arxiv_result_str[:100]}...")
                     results['arxiv_papers'] = [{"raw_output": arxiv_result_str}] # Store raw output if not JSON
                     results['errors'].append(f"ArXiv tool output format unexpected.")
                logger.debug(f"ArXiv search successful, found {len(results['arxiv_papers'])} items.")
            except Exception as e:
                logger.error(f"Error running ArXiv tool: {e}", exc_info=True)
                results['errors'].append(f"ArXiv search failed: {e}")
        elif arxiv_query:
             logger.warning("ArXiv query provided, but ArxivSearchTool is not available.")
             results['errors'].append("ArXiv tool not available.")

        # Run GitHub Search
        if github_query and github_tool:
            try:
                logger.info(f"Running GitHub search with query: '{github_query}'")
                github_result_str = github_tool.run(f"{{"query": "{github_query}", "max_results": {max_res}}}")
                try:
                    results['github_repos'] = json.loads(github_result_str)
                except json.JSONDecodeError:
                     logger.warning(f"GitHub tool returned non-JSON string: {github_result_str[:100]}...")
                     results['github_repos'] = [{"raw_output": github_result_str}]
                     results['errors'].append(f"GitHub tool output format unexpected.")
                logger.debug(f"GitHub search successful, found {len(results['github_repos'])} items.")
            except Exception as e:
                logger.error(f"Error running GitHub tool: {e}", exc_info=True)
                results['errors'].append(f"GitHub search failed: {e}")
        elif github_query:
            logger.warning("GitHub query provided, but GitHubTrendTool is not available.")
            results['errors'].append("GitHub tool not available.")

        # Run News Search
        if news_query and news_tool:
            try:
                logger.info(f"Running News search with query: '{news_query}'")
                news_result_str = news_tool.run(news_query) # Serper tool takes query directly
                try:
                    # Serper tool output needs parsing - assuming it returns a dict-like structure
                    # Adjust parsing based on actual SerperTool output format
                    parsed_news = json.loads(news_result_str) 
                    results['news_articles'] = parsed_news.get('organic', []) # Example: Extract organic results
                except json.JSONDecodeError:
                    logger.warning(f"News tool returned non-JSON string: {news_result_str[:100]}...")
                    results['news_articles'] = [{"raw_output": news_result_str}] 
                    results['errors'].append(f"News tool output format unexpected.")
                logger.debug(f"News search successful, found {len(results['news_articles'])} items.")
            except Exception as e:
                logger.error(f"Error running News tool: {e}", exc_info=True)
                results['errors'].append(f"News search failed: {e}")
        elif news_query:
            logger.warning("News query provided, but SerperSearchTool is not available (check API key?).")
            results['errors'].append("News search tool not available or API key missing.")

        # Log collected counts
        logger.info(
            f"Collection finished. Papers: {len(results.get('arxiv_papers', []))}, "
            f"Repos: {len(results.get('github_repos', []))}, "
            f"News: {len(results.get('news_articles', []))}."
        )
        if results['errors']:
            logger.warning(f"Collection completed with errors: {results['errors']}")
            
        return results

    def analyze_trends(self, trend_data: Dict[str, Any], analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Analyzes the collected trend data using the TrendAnalyzerTool.

        Args:
            trend_data (Dict[str, Any]): The dictionary containing collected data 
                                          (e.g., from collect_trend_data).
            analysis_type (str): The type of analysis desired (e.g., 'brief', 'comprehensive').
                                 This is passed to the analyzer tool.

        Returns:
            Dict[str, Any]: A dictionary containing the analysis summary or an error message.
                            Example success: {'analysis_summary': '...'}
                            Example error: {'error': 'Analysis failed: ...'}
        """
        logger.info(f"Starting trend analysis (type: {analysis_type})...")

        analyzer_tool = next((t for t in self.tools if t.name == 'trend_analyzer'), None)

        if not analyzer_tool:
            logger.error("TrendAnalyzerTool is not available. Cannot perform analysis.")
            return {"error": "Analysis tool is not configured or failed to initialize."}

        # Prepare data for the analyzer tool - needs to be a JSON string
        # Combine relevant data from the input dictionary
        analysis_input_data = {
            "arxiv_data": trend_data.get('arxiv_papers', []),
            "github_data": trend_data.get('github_repos', []),
            "news_data": trend_data.get('news_articles', [])
        }

        # Add analysis_type to the input for the tool if its prompt expects it
        # analysis_input_data["analysis_type"] = analysis_type 
        
        try:
            analysis_input_json = json.dumps(analysis_input_data)
        except TypeError as e:
             logger.error(f"Could not serialize trend data to JSON for analysis: {e}")
             return {"error": f"Data serialization error: {e}"}
             
        try:
            # Construct the input string for the tool, potentially including the analysis type
            # The exact format depends on how the TrendAnalyzerTool expects its input.
            # Assuming it takes a JSON string representing the dictionary.
            tool_input = analysis_input_json
            # If the tool expects type as part of the string: f'{{"data": {analysis_input_json}, "type": "{analysis_type}"}}'

            logger.debug(f"Calling TrendAnalyzerTool with input size: {len(tool_input)} chars")
            # The tool's _run method should return a string (hopefully JSON containing the analysis)
            analysis_result_str = analyzer_tool.run(tool_input)
            logger.info("Trend analysis tool executed.")

            # Attempt to parse the result string as JSON
            try:
                analysis_result = json.loads(analysis_result_str)
                # Check if the result itself contains an error reported by the tool
                if isinstance(analysis_result, dict) and analysis_result.get('error'):
                     logger.error(f"TrendAnalyzerTool reported an error: {analysis_result['error']}")
                     return {"error": f"Analysis failed: {analysis_result['error']}"} 
                # Assuming successful analysis is in a specific key, e.g., 'analysis_summary'
                # Adapt this based on the actual output structure of TrendAnalyzerTool
                if isinstance(analysis_result, dict) and 'analysis_summary' in analysis_result:
                     return {"analysis_summary": analysis_result['analysis_summary']}
                else:
                     # If structure is different or just a string summary
                     return {"analysis_summary": analysis_result_str} 

            except json.JSONDecodeError:
                # If the tool returned a non-JSON string, return it directly as the summary
                logger.warning("TrendAnalyzerTool returned a non-JSON string. Returning raw output.")
                return {"analysis_summary": analysis_result_str}

        except Exception as e:
            logger.error(f"Error during trend analysis execution: {e}", exc_info=True)
            error_message = f"Error analyzing trends: {e}. Check logs for details."
            if "rate limit" in str(e).lower():
                error_message = "Analysis failed due to API rate limits. Please check your OpenAI plan or try again later."
            elif "api key" in str(e).lower():
                 error_message = "Analysis failed due to an API key error. Please ensure your OpenAI API key is correct."
            return {"error": error_message}
