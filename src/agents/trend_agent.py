"""
Trend Agent - Main agent for orchestrating tools in the Scout-Edge platform.
"""
import logging
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.chains.conversation.memory import ConversationSummaryMemory
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool

# Import configuration settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Import tools
from tools.arxiv_tool import ArxivSearchTool
from tools.github_tool import GitHubTrendTool
from tools.serper_search_tool import SerperSearchTool
from tools.trend_analyzer_tool import TrendAnalyzerTool

logger = logging.getLogger(__name__)


class TrendAgent:
    """
    Main agent for orchestrating AI trend tracking tools.
    
    This agent uses LangChain to coordinate various tools for collecting and 
    analyzing data from different sources like ArXiv, GitHub, news articles, etc.
    """
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize the TrendAgent with tools and LLM.
        
        Args:
            api_keys (Dict[str, str], optional): Dictionary of API keys
        """
        self.api_keys = api_keys or {}
        self.tools = self._initialize_tools()
        self.llm = self._initialize_llm()
        self.memory = self._initialize_memory()
        self.agent = self._initialize_agent()
        
    def _initialize_tools(self) -> List[BaseTool]:
        """
        Initialize all tools used by the trend agent.
        
        Returns:
            List[BaseTool]: List of initialized tools
        """
        try:
            # Initialize all tools
            arxiv_tool = ArxivSearchTool()
            github_tool = GitHubTrendTool(api_key=self.api_keys.get('github') or config.GITHUB_API_KEY)
            serper_tool = SerperSearchTool(api_key=self.api_keys.get('serper') or config.SERPER_API_KEY)
            trend_analyzer = TrendAnalyzerTool()
            
            # Return list of all tools
            tools = [
                arxiv_tool,
                github_tool,
                serper_tool,
                trend_analyzer
            ]
            
            logger.info(f"Initialized {len(tools)} tools successfully")
            return tools
            
        except Exception as e:
            logger.error(f"Error initializing tools: {str(e)}")
            # Return any tools that could be initialized
            return []
    
    def _initialize_llm(self):
        """
        Initialize the language model for the agent.
        
        Returns:
            BaseLLM: Initialized language model
        """
        try:
            llm = ChatOpenAI(
                model_name=config.LLM_MODEL,
                temperature=config.LLM_TEMPERATURE,
                api_key=self.api_keys.get('openai') or config.OPENAI_API_KEY
            )
            logger.info(f"Initialized LLM: {config.LLM_MODEL}")
            return llm
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            return None
    
    def _initialize_memory(self):
        """
        Initialize the memory for the agent.
        
        Returns:
            BaseChatMemory: Initialized memory
        """
        try:
            # Use conversation summary memory for efficiency with long conversations
            memory = ConversationSummaryMemory(
                llm=self.llm,
                memory_key="chat_history",
                return_messages=True
            )
            logger.info("Initialized conversation summary memory")
            return memory
        except Exception as e:
            logger.error(f"Error initializing memory: {str(e)}")
            # Fallback to simpler memory if summary memory fails
            return ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    def _initialize_agent(self):
        """
        Initialize the LangChain agent with tools and memory.
        
        Returns:
            Agent: Initialized agent
        """
        if not self.llm or not self.tools:
            logger.error("Cannot initialize agent: LLM or tools not available")
            return None
            
        try:
            agent = initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                memory=self.memory,
                verbose=config.VERBOSE_MODE,
                handle_parsing_errors=True
            )
            
            logger.info("Agent initialized successfully")
            return agent
        except Exception as e:
            logger.error(f"Error initializing agent: {str(e)}")
            return None
    
    def run(self, query: str) -> Dict[str, Any]:
        """
        Run the agent with a specific query.
        
        Args:
            query (str): User query or command
            
        Returns:
            Dict[str, Any]: Agent response and metadata
        """
        if not self.agent:
            error_msg = "Agent not initialized properly. Check logs for details."
            logger.error(error_msg)
            return {"error": error_msg, "success": False}
            
        try:
            # Execute the agent
            start_time = datetime.now()
            response = self.agent.run(input=query)
            end_time = datetime.now()
            
            # Format response
            execution_time = (end_time - start_time).total_seconds()
            result = {
                "response": response,
                "execution_time": execution_time,
                "timestamp": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "query": query,
                "success": True
            }
            
            logger.info(f"Agent executed query in {execution_time:.2f} seconds")
            return result
            
        except Exception as e:
            error_msg = f"Error executing agent: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "query": query, "success": False}
    
    def collect_trend_data(self, 
                          arxiv_query: str = "artificial intelligence", 
                          github_query: str = "machine learning", 
                          news_query: str = "AI trends", 
                          max_results: int = 10) -> Dict[str, Any]:
        """
        Collect trend data from multiple sources.
        
        Args:
            arxiv_query (str): Query for ArXiv papers
            github_query (str): Query for GitHub repositories
            news_query (str): Query for news articles
            max_results (int): Maximum number of results per source
            
        Returns:
            Dict[str, Any]: Collected trend data
        """
        try:
            results = {}
            
            # Get ArXiv data
            try:
                arxiv_tool = next((tool for tool in self.tools if tool.name == "arxiv"), None)
                if arxiv_tool:
                    arxiv_results = arxiv_tool._run(
                        query=arxiv_query, 
                        max_results=max_results, 
                        days_back=30
                    )
                    results["arxiv_data"] = arxiv_results
                    logger.info(f"Collected {len(arxiv_results)} ArXiv papers")
            except Exception as e:
                logger.error(f"Error collecting ArXiv data: {str(e)}")
                results["arxiv_data"] = {"error": str(e)}
            
            # Get GitHub data
            try:
                github_tool = next((tool for tool in self.tools if tool.name == "github"), None)
                if github_tool:
                    github_results = github_tool._run(
                        query=github_query, 
                        max_results=max_results, 
                        days_back=30
                    )
                    results["github_data"] = github_results
                    logger.info(f"Collected {len(github_results)} GitHub repositories")
            except Exception as e:
                logger.error(f"Error collecting GitHub data: {str(e)}")
                results["github_data"] = {"error": str(e)}
            
            # Get news data
            try:
                serper_tool = next((tool for tool in self.tools if tool.name == "serper_search"), None)
                if serper_tool:
                    news_results = serper_tool._run(
                        query=news_query,
                        search_type="news",
                        num_results=max_results
                    )
                    results["news_data"] = news_results
                    logger.info(f"Collected {len(news_results)} news articles")
            except Exception as e:
                logger.error(f"Error collecting news data: {str(e)}")
                results["news_data"] = {"error": str(e)}
            
            return results
            
        except Exception as e:
            error_msg = f"Error collecting trend data: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def analyze_trends(self, trend_data: Dict[str, Any], analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Analyze collected trend data.
        
        Args:
            trend_data (Dict[str, Any]): Collected trend data
            analysis_type (str): Type of analysis to perform
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            analyzer_tool = next((tool for tool in self.tools if tool.name == "trend_analyzer"), None)
            if not analyzer_tool:
                error_msg = "Trend analyzer tool not available"
                logger.error(error_msg)
                return {"error": error_msg}
                
            analysis = analyzer_tool._run(trend_data, analysis_type=analysis_type)
            logger.info(f"Completed {analysis_type} trend analysis")
            return analysis
            
        except Exception as e:
            error_msg = f"Error analyzing trends: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
