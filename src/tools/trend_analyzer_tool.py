"""
Trend analysis tool - Tool for analyzing AI trends for the Scout-Edge platform.
"""
import logging
import sys
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain.tools import BaseTool
from langchain.llms.base import BaseLLM
from langchain_openai import ChatOpenAI

# Import configuration settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


class TrendAnalyzerTool(BaseTool):
    """
    LangChain tool for analyzing AI trends collected from different sources.
    """
    name = "trend_analyzer"
    description = "Analyzes and summarizes artificial intelligence trend data collected from various data sources."
    
    def __init__(self, llm: Optional[BaseLLM] = None):
        """
        Initialize the TrendAnalyzerTool class.
        
        Args:
            llm (BaseLLM, optional): Language model to use for analysis
        """
        super().__init__()
        
        # If llm is not specified, create one using the OpenAI API
        if llm is None:
            try:
                self.llm = ChatOpenAI(
                    model_name=config.LLM_MODEL,
                    temperature=config.LLM_TEMPERATURE
                )
            except Exception as e:
                logger.error(f"Error initializing LLM: {str(e)}")
                self.llm = None
        else:
            self.llm = llm
            
    def _run(self, trend_data: Dict[str, Any], 
             analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Analyze trend data.
        
        Args:
            trend_data (Dict[str, Any]): Trend data to analyze
            analysis_type (str): Analysis type (brief, comprehensive, technical, business)
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        # If no LLM is available, perform a basic analysis
        if self.llm is None:
            return self._basic_analysis(trend_data)
            
        try:
            # Prepare prompt for LLM
            prompt = self._prepare_prompt(trend_data, analysis_type)
            
            # Call LLM
            analysis = self.llm.invoke(prompt)
            
            # Structure the result
            result = {
                "analysis": analysis,
                "analysis_type": analysis_type,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_points": len(trend_data),
                "success": True
            }
            
            logger.info(f"{analysis_type} trend analysis completed successfully.")
            return result
            
        except Exception as e:
            error_msg = f"Error during trend analysis: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "success": False}
    
    async def _arun(self, trend_data: Dict[str, Any], 
                   analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Async method required for the tool (currently calls the sync method)"""
        return self._run(trend_data, analysis_type)
    
    def _prepare_prompt(self, trend_data: Dict[str, Any], analysis_type: str) -> str:
        """
        Prepare analysis prompt for LLM.
        
        Args:
            trend_data (Dict[str, Any]): Trend data to analyze
            analysis_type (str): Analysis type
            
        Returns:
            str: Prepared prompt
        """
        # Different prompts for different analysis types
        if analysis_type == "brief":
            system_prompt = "Briefly summarize current trends in the AI field (3-5 sentences). Highlight important points."
        elif analysis_type == "technical":
            system_prompt = "Analyze current trends in the AI field from a technical perspective. Focus on new technologies, algorithms, and methods."
        elif analysis_type == "business":
            system_prompt = "Analyze current trends in the AI field from a business perspective. Focus on commercial potential, investment opportunities, and market impacts."
        else:  # comprehensive
            system_prompt = """
            Comprehensively analyze current trends in the AI field.
            
            Please address the following topics:
            1. What are the major emerging trends?
            2. What are the rising technologies and approaches?
            3. What potential future impacts might these trends have?
            4. Which research areas or projects are particularly noteworthy?
            5. What recommendations can you offer to professionals and researchers in the AI field based on this information?
            
            Present the analysis in a clear, structured, and informative manner.
            """
        
        # Format the data
        formatted_data = json.dumps(trend_data, indent=2, ensure_ascii=False)
        
        # Create the full prompt
        full_prompt = f"{system_prompt}\n\nHERE IS THE DATA TO ANALYZE:\n{formatted_data}"
        return full_prompt
    
    def _basic_analysis(self, trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a basic analysis without LLM.
        
        Args:
            trend_data (Dict[str, Any]): Trend data to analyze
            
        Returns:
            Dict[str, Any]: Basic analysis results
        """
        # Count data sources
        sources = set()
        item_counts = {}
        
        # Collect data sources and item counts
        for key, value in trend_data.items():
            if isinstance(value, list):
                item_counts[key] = len(value)
                for item in value:
                    if isinstance(item, dict) and "source" in item:
                        sources.add(item["source"])
        
        # Basic analysis result
        analysis = {
            "total_sources": len(sources),
            "sources": list(sources),
            "item_counts": item_counts,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "analysis_note": "This is a basic analysis result. A more comprehensive analysis requires an LLM."
        }
        
        return analysis


class TrendDashboard:
    """
    Class for visualizing and reporting trend analysis results.
    """
    def __init__(self):
        """
        Initialize the TrendDashboard class.
        """
        self.analyzer = TrendAnalyzerTool()
    
    def generate_trend_report(self, arxiv_data: Dict[str, Any], 
                             github_data: Dict[str, Any], 
                             news_data: Dict[str, Any], 
                             huggingface_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a trend report by combining data from different sources.
        
        Args:
            arxiv_data (Dict[str, Any]): ArXiv trend data
            github_data (Dict[str, Any]): GitHub trend data
            news_data (Dict[str, Any]): News trend data
            huggingface_data (Dict[str, Any], optional): HuggingFace trend data
            
        Returns:
            Dict[str, Any]: Generated trend report
        """
        # Combine all data
        combined_data = {
            "arxiv_trends": arxiv_data,
            "github_trends": github_data,
            "news_trends": news_data
        }
        
        if huggingface_data:
            combined_data["huggingface_trends"] = huggingface_data
        
        # Analyze with LLM
        analysis = self.analyzer._run(combined_data, analysis_type="comprehensive")
        
        # Add report creation time
        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "report_title": "Current AI Field Trend Analysis",
            "analysis": analysis,
            "data_sources": list(combined_data.keys()),
            "raw_data": combined_data
        }
        
        return report
    
    def generate_summary(self, trend_report: Dict[str, Any]) -> str:
        """
        Extract a brief summary from a trend report.
        
        Args:
            trend_report (Dict[str, Any]): Trend report
            
        Returns:
            str: Brief summary
        """
        # Extract a brief summary using LLM
        if self.analyzer.llm:
            analysis_data = trend_report.get("analysis", {})
            if "analysis" in analysis_data:
                full_analysis = analysis_data["analysis"]
                
                prompt = f"""
                Transform the following AI trend analysis report into a brief 3-5 sentence summary:
                
                {full_analysis}
                
                IMPORTANT: The summary should be brief, clear, and focused on the most important trends.
                """
                
                summary = self.analyzer.llm.invoke(prompt)
                return summary
        
        # Create a simple summary if LLM is not available or analysis cannot be extracted
        sources_count = len(trend_report.get("data_sources", []))
        return f"Analysis of recent AI trends based on data from {sources_count} different sources. See the full analysis for detailed report."
