"""
Memory module - Provides memory management for the Scout-Edge platform agents.
"""
import logging
import os
import sys
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.memory.chat_message_histories import FileChatMessageHistory
from langchain_openai import ChatOpenAI

# Import configuration settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


class AgentMemory:
    """
    Memory management for AI agents in the Scout-Edge platform.
    
    This class provides persistent memory storage and retrieval for AI agents,
    allowing for context maintenance across sessions and effective trend tracking.
    """
    
    def __init__(self, 
                agent_id: str,
                llm: Optional[Any] = None,
                memory_dir: Optional[str] = None,
                use_summary: bool = True):
        """
        Initialize the AgentMemory.
        
        Args:
            agent_id (str): Unique identifier for the agent
            llm (Any, optional): Language model for summarization
            memory_dir (str, optional): Directory to store memory files
            use_summary (bool): Whether to use summary memory or buffer memory
        """
        self.agent_id = agent_id
        self.llm = llm
        
        # Create memory directory if it doesn't exist
        self.memory_dir = memory_dir or os.path.join(
            config.DATA_DIR, "memory"
        )
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # Initialize memory files
        self.chat_file = os.path.join(self.memory_dir, f"{agent_id}_chat.json")
        self.trend_file = os.path.join(self.memory_dir, f"{agent_id}_trends.json")
        self.context_file = os.path.join(self.memory_dir, f"{agent_id}_context.json")
        
        # Initialize memory systems
        self.memory = self._initialize_memory(use_summary)
        self.trends = self._load_trends()
        self.context = self._load_context()
        
        logger.info(f"Initialized AgentMemory for agent {agent_id}")
    
    def _initialize_memory(self, use_summary: bool):
        """
        Initialize the appropriate memory system.
        
        Args:
            use_summary (bool): Whether to use summary memory
            
        Returns:
            BaseChatMemory: Initialized memory
        """
        try:
            # Initialize file-based chat message history
            message_history = FileChatMessageHistory(self.chat_file)
            
            if use_summary and self.llm:
                # Use conversation summary memory
                memory = ConversationSummaryMemory(
                    llm=self.llm,
                    memory_key="chat_history",
                    return_messages=True,
                    chat_memory=message_history
                )
                logger.info("Using conversation summary memory")
            else:
                # Fallback to buffer memory
                memory = ConversationBufferMemory(
                    memory_key="chat_history", 
                    return_messages=True,
                    chat_memory=message_history
                )
                logger.info("Using conversation buffer memory")
                
            return memory
            
        except Exception as e:
            logger.error(f"Error initializing memory: {str(e)}")
            # Fallback to in-memory buffer
            return ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
    
    def _load_trends(self) -> Dict[str, Any]:
        """
        Load trends from the trend file.
        
        Returns:
            Dict[str, Any]: Loaded trends
        """
        try:
            if os.path.exists(self.trend_file):
                with open(self.trend_file, 'r') as f:
                    return json.load(f)
            else:
                # Initialize with empty trends dictionary
                trends = {
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "trends": []
                }
                self._save_trends(trends)
                return trends
        except Exception as e:
            logger.error(f"Error loading trends: {str(e)}")
            return {"last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "trends": []}
    
    def _save_trends(self, trends: Dict[str, Any]) -> bool:
        """
        Save trends to the trend file.
        
        Args:
            trends (Dict[str, Any]): Trends to save
            
        Returns:
            bool: Success status
        """
        try:
            with open(self.trend_file, 'w') as f:
                json.dump(trends, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving trends: {str(e)}")
            return False
    
    def _load_context(self) -> Dict[str, Any]:
        """
        Load context from the context file.
        
        Returns:
            Dict[str, Any]: Loaded context
        """
        try:
            if os.path.exists(self.context_file):
                with open(self.context_file, 'r') as f:
                    return json.load(f)
            else:
                # Initialize with empty context dictionary
                context = {
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_preferences": {},
                    "session_data": {}
                }
                self._save_context(context)
                return context
        except Exception as e:
            logger.error(f"Error loading context: {str(e)}")
            return {"last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                   "user_preferences": {}, "session_data": {}}
    
    def _save_context(self, context: Dict[str, Any]) -> bool:
        """
        Save context to the context file.
        
        Args:
            context (Dict[str, Any]): Context to save
            
        Returns:
            bool: Success status
        """
        try:
            with open(self.context_file, 'w') as f:
                json.dump(context, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving context: {str(e)}")
            return False
    
    def add_message(self, role: str, content: str) -> bool:
        """
        Add a message to the memory.
        
        Args:
            role (str): Role of the message sender (human or ai)
            content (str): Content of the message
            
        Returns:
            bool: Success status
        """
        try:
            if role.lower() == "human":
                self.memory.chat_memory.add_user_message(content)
            else:
                self.memory.chat_memory.add_ai_message(content)
            return True
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            return False
    
    def add_trend(self, trend: Dict[str, Any]) -> bool:
        """
        Add a trend to the trends memory.
        
        Args:
            trend (Dict[str, Any]): Trend to add
            
        Returns:
            bool: Success status
        """
        try:
            # Add timestamp if not present
            if "timestamp" not in trend:
                trend["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
            self.trends["trends"].append(trend)
            self.trends["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return self._save_trends(self.trends)
        except Exception as e:
            logger.error(f"Error adding trend: {str(e)}")
            return False
    
    def update_user_preference(self, key: str, value: Any) -> bool:
        """
        Update or add a user preference.
        
        Args:
            key (str): Preference key
            value (Any): Preference value
            
        Returns:
            bool: Success status
        """
        try:
            self.context["user_preferences"][key] = value
            self.context["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return self._save_context(self.context)
        except Exception as e:
            logger.error(f"Error updating user preference: {str(e)}")
            return False
    
    def update_session_data(self, key: str, value: Any) -> bool:
        """
        Update or add session data.
        
        Args:
            key (str): Data key
            value (Any): Data value
            
        Returns:
            bool: Success status
        """
        try:
            self.context["session_data"][key] = value
            self.context["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return self._save_context(self.context)
        except Exception as e:
            logger.error(f"Error updating session data: {str(e)}")
            return False
    
    def get_recent_trends(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent trends.
        
        Args:
            n (int): Number of trends to return
            
        Returns:
            List[Dict[str, Any]]: Recent trends
        """
        try:
            # Sort trends by timestamp (most recent first)
            sorted_trends = sorted(
                self.trends["trends"], 
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )
            return sorted_trends[:n]
        except Exception as e:
            logger.error(f"Error getting recent trends: {str(e)}")
            return []
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """
        Get the chat history.
        
        Returns:
            List[Dict[str, str]]: Chat history messages
        """
        try:
            messages = self.memory.chat_memory.messages
            return [{"role": msg.type, "content": msg.content} for msg in messages]
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            return []
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """
        Get user preferences.
        
        Returns:
            Dict[str, Any]: User preferences
        """
        return self.context.get("user_preferences", {})
    
    def clear_memory(self, keep_preferences: bool = True) -> bool:
        """
        Clear the memory but optionally keep user preferences.
        
        Args:
            keep_preferences (bool): Whether to keep user preferences
            
        Returns:
            bool: Success status
        """
        try:
            # Clear chat history
            self.memory.chat_memory.clear()
            
            # Clear trends
            self.trends = {
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "trends": []
            }
            self._save_trends(self.trends)
            
            # Clear context but optionally keep preferences
            user_prefs = self.context.get("user_preferences", {}) if keep_preferences else {}
            self.context = {
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_preferences": user_prefs,
                "session_data": {}
            }
            self._save_context(self.context)
            
            logger.info(f"Memory cleared for agent {self.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing memory: {str(e)}")
            return False


class TrendMemoryManager:
    """
    Manager for trend memories across multiple agents.
    
    This class allows for the consolidation and analysis of trends
    from different agent memories.
    """
    
    def __init__(self, memory_dir: Optional[str] = None):
        """
        Initialize the TrendMemoryManager.
        
        Args:
            memory_dir (str, optional): Directory containing memory files
        """
        self.memory_dir = memory_dir or os.path.join(
            config.DATA_DIR, "memory"
        )
        
    def get_all_agent_ids(self) -> List[str]:
        """
        Get all agent IDs from memory files.
        
        Returns:
            List[str]: List of agent IDs
        """
        try:
            agent_ids = set()
            
            # Get all trend files
            trend_files = Path(self.memory_dir).glob("*_trends.json")
            for file in trend_files:
                # Extract agent ID from filename
                filename = os.path.basename(file)
                agent_id = filename.replace("_trends.json", "")
                agent_ids.add(agent_id)
                
            return list(agent_ids)
        except Exception as e:
            logger.error(f"Error getting agent IDs: {str(e)}")
            return []
    
    def consolidate_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Consolidate trends from all agents.
        
        Args:
            days (int): Number of days to look back
            
        Returns:
            Dict[str, Any]: Consolidated trends
        """
        try:
            all_trends = []
            agent_ids = self.get_all_agent_ids()
            
            # Get current date for comparison
            current_date = datetime.now()
            
            # Collect trends from all agents
            for agent_id in agent_ids:
                trend_file = os.path.join(self.memory_dir, f"{agent_id}_trends.json")
                if os.path.exists(trend_file):
                    with open(trend_file, 'r') as f:
                        agent_trends = json.load(f)
                        
                    # Filter trends by date
                    for trend in agent_trends.get("trends", []):
                        try:
                            trend_date = datetime.strptime(
                                trend.get("timestamp", ""), 
                                "%Y-%m-%d %H:%M:%S"
                            )
                            days_diff = (current_date - trend_date).days
                            
                            if days_diff <= days:
                                # Add agent_id to the trend
                                trend["agent_id"] = agent_id
                                all_trends.append(trend)
                        except Exception:
                            # Skip trends with invalid timestamps
                            continue
            
            # Sort by timestamp
            all_trends.sort(
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )
            
            # Create consolidated trends dictionary
            consolidated = {
                "consolidated_date": current_date.strftime("%Y-%m-%d %H:%M:%S"),
                "lookback_days": days,
                "trend_count": len(all_trends),
                "agent_count": len(agent_ids),
                "trends": all_trends
            }
            
            return consolidated
        except Exception as e:
            logger.error(f"Error consolidating trends: {str(e)}")
            return {
                "consolidated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e),
                "trends": []
            }
    
    def export_consolidated_trends(self, output_file: str, days: int = 30) -> bool:
        """
        Export consolidated trends to a file.
        
        Args:
            output_file (str): Output file path
            days (int): Number of days to look back
            
        Returns:
            bool: Success status
        """
        try:
            consolidated = self.consolidate_trends(days)
            
            with open(output_file, 'w') as f:
                json.dump(consolidated, f, indent=2)
                
            logger.info(f"Exported {consolidated['trend_count']} consolidated trends to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting consolidated trends: {str(e)}")
            return False
