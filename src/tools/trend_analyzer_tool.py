import logging
import json
from typing import Any, Optional

from langchain.tools import BaseTool
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI

# Setup logging
logger = logging.getLogger(__name__)


class TrendAnalyzerTool(BaseTool):
    """Tool for analyzing trends based on collected data (e.g., research papers, articles)."""
    name: str = "trend_analyzer"
    description: str = (
        "Analyzes a list of items (like research papers or news articles) "
        "to identify key trends, themes, and insights."
    )
    llm: Optional[OpenAI] = None  # Define llm at class level

    def __init__(self, llm: Optional[OpenAI] = None, **kwargs: Any):
        """Initialize the tool with an optional language model."""
        super().__init__(**kwargs)
        # Allow llm to be passed or default to a new OpenAI instance
        self.llm = llm or OpenAI(temperature=0.7)
        if not self.llm:
            logger.warning(
                "LLM not provided for TrendAnalyzerTool. Analysis will be basic."
            )

    def _run(self, data: str) -> str:
        """
        Analyzes the provided data string (expected to be JSON) to identify trends.

        Args:
            data: A string containing JSON data, typically a dictionary containing lists 
                  of items (e.g., {"arxiv_data": [...], "github_data": [...]}).

        Returns:
            A string containing the analysis summary.
        """
        logger.info(f"Received data for analysis: {data[:200]}...")  # Log snippet

        all_items = []
        try:
            # Attempt to parse the input string as JSON (expecting a dictionary)
            data_dict = json.loads(data)
            if not isinstance(data_dict, dict):
                # Handle case where input isn't a dictionary as expected
                logger.error("Input data is not a valid JSON dictionary.")
                # Optionally, try treating it as a list if that's a possible fallback
                if isinstance(data_dict, list):
                     logger.info("Input was a JSON list, processing items directly.")
                     all_items = data_dict
                else:
                     return "Error: Input data is not a valid JSON dictionary or list."
            else:
                # Extract items from known list keys within the dictionary
                for key, value in data_dict.items():
                    if isinstance(value, list):
                        logger.info(f"Extracted {len(value)} items from key '{key}'.")
                        all_items.extend(value)
                    else:
                        logger.warning(f"Value for key '{key}' is not a list, skipping.")
                
                if not all_items:
                     return "Error: No lists of items found within the input JSON dictionary."
                     
                logger.info(f"Successfully parsed a total of {len(all_items)} items from JSON data.")

        except json.JSONDecodeError:
            logger.error("Failed to decode input data as JSON.")
            return "Error: Failed to decode input data as JSON."
        except Exception as e:
            logger.error(f"Unexpected error parsing data: {e}")
            return f"Error processing input data: {e}"

        # Prepare data for LLM input (combine relevant fields from all items)
        # Ensure items are dictionaries before accessing keys
        analysis_input = "\n\n".join(
            f"Title: {item.get('title', 'N/A')}\n"
            f"Summary: {item.get('summary', item.get('abstract', item.get('description', 'N/A')))}" # Added 'description' for GitHub
            for item in all_items if isinstance(item, dict) # Process only dict items
        )[:4000] # Limit input size for LLM (adjust size as needed)

        if not analysis_input:
             return "No valid content found in the items for analysis."

        if not self.llm:
            logger.warning("LLM not available. Performing basic analysis.")
            # Basic analysis if LLM is not available
            summary = f"Analyzed {len(all_items)} potential items. "
            summary += "Key themes could not be extracted without an LLM."
            return summary

        # Define the prompt for the LLM
        prompt_template = PromptTemplate(
            input_variables=["documents"],
            template=(
                "Analyze the following collection of document titles and summaries/descriptions "
                "to identify the main trends, key themes, and emerging topics. "
                "Provide a concise summary of your findings.\n\n"
                "Documents:\n{documents}\n\nAnalysis Summary:"
            )
        )

        # Create and run the LLM chain
        chain = LLMChain(llm=self.llm, prompt=prompt_template)

        try:
            logger.info(f"Running LLM chain for trend analysis with {len(analysis_input)} characters of input...")
            result = chain.run(documents=analysis_input)
            logger.info("Trend analysis completed by LLM.")
            return result
        except Exception as e:
            logger.error(f"Error during LLM analysis: {e}", exc_info=True)
            return f"Error during analysis: {e}"

    async def _arun(self, data: str) -> str:
        """Asynchronous version of the analysis logic."""
        # For simplicity, call the synchronous version for now.
        logger.info("Async analysis request, running sync version.")
        return self._run(data)
