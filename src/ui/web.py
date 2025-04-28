"""
Web interface for Scout-Edge - AI trend tracking system.
Built with Streamlit for a simple, interactive experience.
"""
import os
import sys
import json
import logging
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Import configuration settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Import agent
from agents.trend_agent import TrendAgent
from agents.memory import TrendMemoryManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize session state
def init_session_state():
    """Initialize Streamlit session state variables."""
    if 'agent' not in st.session_state:
        try:
            st.session_state.agent = TrendAgent()
        except Exception as e:
            st.error(f"Error initializing agent: {str(e)}")
            st.session_state.agent = None
    
    if 'memory_manager' not in st.session_state:
        try:
            st.session_state.memory_manager = TrendMemoryManager()
        except Exception as e:
            st.error(f"Error initializing memory manager: {str(e)}")
            st.session_state.memory_manager = None
    
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "Query"
    
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    if 'collected_data' not in st.session_state:
        st.session_state.collected_data = None
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None


# Interface Components
def render_header():
    """Render the application header."""
    st.title("Scout-Edge: AI Trend Tracking System")
    st.markdown("""
    Track and analyze emerging trends in artificial intelligence research, 
    development, and industry news.
    """)
    st.markdown("---")


def render_tabs():
    """Render navigation tabs."""
    tabs = ["Query", "Collect Trends", "Analyze Trends", "View History"]
    
    cols = st.columns(len(tabs))
    for i, tab in enumerate(tabs):
        if cols[i].button(
            tab, 
            use_container_width=True,
            type="primary" if st.session_state.current_tab == tab else "secondary"
        ):
            st.session_state.current_tab = tab
            st.experimental_rerun()


def render_query_tab():
    """Render the query interface."""
    st.header("Ask About AI Trends")
    
    with st.form("query_form"):
        query = st.text_area(
            "Enter your question about AI trends:",
            height=100,
            placeholder="E.g., What are the current trends in generative AI?"
        )
        
        submitted = st.form_submit_button("Submit Query")
        
        if submitted and query:
            with st.spinner("Processing your query..."):
                try:
                    results = st.session_state.agent.run(query)
                    
                    # Save to history
                    history_item = {
                        "type": "query",
                        "query": query,
                        "results": results,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.query_history.append(history_item)
                    
                    # Display results
                    if "error" in results:
                        st.error(results["error"])
                    else:
                        st.success("Query processed successfully!")
                        st.subheader("Response")
                        st.write(results.get("response", "No response generated"))
                        
                        if "execution_time" in results:
                            st.caption(f"Execution time: {results['execution_time']:.2f} seconds")
                except Exception as e:
                    st.error(f"Error processing query: {str(e)}")


def render_collect_tab():
    """Render the data collection interface."""
    st.header("Collect AI Trend Data")
    
    with st.form("collect_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            arxiv_query = st.text_input(
                "ArXiv Query:", 
                value="artificial intelligence",
                help="Search query for research papers"
            )
            
            github_query = st.text_input(
                "GitHub Query:", 
                value="machine learning",
                help="Search query for GitHub repositories"
            )
        
        with col2:
            news_query = st.text_input(
                "News Query:", 
                value="AI trends",
                help="Search query for news articles"
            )
            
            max_results = st.slider(
                "Max Results per Source:", 
                min_value=5, 
                max_value=50, 
                value=10,
                help="Maximum number of results to fetch from each source"
            )
        
        submitted = st.form_submit_button("Collect Data")
        
        if submitted:
            with st.spinner("Collecting trend data... This may take a minute."):
                try:
                    results = st.session_state.agent.collect_trend_data(
                        arxiv_query=arxiv_query,
                        github_query=github_query,
                        news_query=news_query,
                        max_results=max_results
                    )
                    
                    # Save collected data
                    st.session_state.collected_data = results
                    
                    # Save to history
                    history_item = {
                        "type": "collect",
                        "queries": {
                            "arxiv": arxiv_query,
                            "github": github_query,
                            "news": news_query
                        },
                        "max_results": max_results,
                        "results": results,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.query_history.append(history_item)
                    
                    # Display summary
                    if "error" in results:
                        st.error(results["error"])
                    else:
                        st.success("Data collection completed!")
                        
                        # Show summary
                        st.subheader("Collection Summary")
                        
                        # Create summary table
                        summary_data = []
                        
                        if "arxiv_data" in results:
                            arxiv_count = len(results["arxiv_data"]) if isinstance(results["arxiv_data"], list) else 0
                            summary_data.append({"Source": "ArXiv", "Items Collected": arxiv_count})
                        
                        if "github_data" in results:
                            github_count = len(results["github_data"]) if isinstance(results["github_data"], list) else 0
                            summary_data.append({"Source": "GitHub", "Items Collected": github_count})
                        
                        if "news_data" in results:
                            news_count = len(results["news_data"]) if isinstance(results["news_data"], list) else 0
                            summary_data.append({"Source": "News", "Items Collected": news_count})
                        
                        # Display summary table
                        st.table(summary_data)
                        
                        # Option to analyze now
                        if st.button("Analyze This Data Now"):
                            st.session_state.current_tab = "Analyze Trends"
                            st.experimental_rerun()
                
                except Exception as e:
                    st.error(f"Error collecting data: {str(e)}")


def render_analyze_tab():
    """Render the analysis interface."""
    st.header("Analyze AI Trends")
    
    # Check if we have data to analyze
    if st.session_state.collected_data is None:
        st.warning("No data available for analysis. Please collect data first.")
        if st.button("Go to Data Collection"):
            st.session_state.current_tab = "Collect Trends"
            st.experimental_rerun()
        return
    
    with st.form("analyze_form"):
        analysis_type = st.selectbox(
            "Analysis Type:",
            options=["comprehensive", "brief", "technical", "business"],
            format_func=lambda x: x.capitalize(),
            help="Type of analysis to perform"
        )
        
        submitted = st.form_submit_button("Analyze Data")
        
        if submitted:
            with st.spinner("Analyzing trend data... This may take a minute."):
                try:
                    results = st.session_state.agent.analyze_trends(
                        trend_data=st.session_state.collected_data,
                        analysis_type=analysis_type
                    )
                    
                    # Save analysis results
                    st.session_state.analysis_results = results
                    
                    # Save to history
                    history_item = {
                        "type": "analyze",
                        "analysis_type": analysis_type,
                        "results": results,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.query_history.append(history_item)
                    
                    # Display results
                    if "error" in results:
                        st.error(results["error"])
                    else:
                        st.success("Analysis completed!")
                        
                        st.subheader("Analysis Results")
                        
                        if "analysis" in results:
                            analysis = results["analysis"]
                            st.markdown(analysis)
                        else:
                            st.write(results)
                        
                        # Option to export
                        if st.button("Export Results"):
                            # Create JSON string
                            json_results = json.dumps(results, indent=2)
                            
                            # Offer download
                            st.download_button(
                                label="Download JSON",
                                data=json_results,
                                file_name=f"trend_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json"
                            )
                
                except Exception as e:
                    st.error(f"Error analyzing data: {str(e)}")


def render_history_tab():
    """Render the history view."""
    st.header("Query and Analysis History")
    
    if not st.session_state.query_history:
        st.info("No history available yet. Try making some queries or analyses.")
        return
    
    # Filter options
    filter_type = st.selectbox(
        "Filter by type:",
        options=["All", "Queries", "Data Collection", "Analysis"],
        index=0
    )
    
    # Apply filters
    filtered_history = st.session_state.query_history
    if filter_type == "Queries":
        filtered_history = [item for item in filtered_history if item["type"] == "query"]
    elif filter_type == "Data Collection":
        filtered_history = [item for item in filtered_history if item["type"] == "collect"]
    elif filter_type == "Analysis":
        filtered_history = [item for item in filtered_history if item["type"] == "analyze"]
    
    # Sort by most recent first
    filtered_history = sorted(
        filtered_history,
        key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S"),
        reverse=True
    )
    
    # Display history items
    for i, item in enumerate(filtered_history):
        with st.expander(
            f"{item['type'].capitalize()} - {item['timestamp']}",
            expanded=(i == 0)  # Expand the most recent by default
        ):
            if item["type"] == "query":
                st.caption("Query")
                st.code(item["query"])
                
                st.caption("Response")
                st.write(item["results"].get("response", "No response"))
                
            elif item["type"] == "collect":
                st.caption("Collection Parameters")
                st.write(f"ArXiv: {item['queries']['arxiv']}")
                st.write(f"GitHub: {item['queries']['github']}")
                st.write(f"News: {item['queries']['news']}")
                st.write(f"Max results per source: {item['max_results']}")
                
                # Show data counts
                st.caption("Collection Results")
                results = item["results"]
                
                if "arxiv_data" in results:
                    arxiv_count = len(results["arxiv_data"]) if isinstance(results["arxiv_data"], list) else 0
                    st.write(f"ArXiv papers: {arxiv_count}")
                
                if "github_data" in results:
                    github_count = len(results["github_data"]) if isinstance(results["github_data"], list) else 0
                    st.write(f"GitHub repositories: {github_count}")
                
                if "news_data" in results:
                    news_count = len(results["news_data"]) if isinstance(results["news_data"], list) else 0
                    st.write(f"News articles: {news_count}")
                
            elif item["type"] == "analyze":
                st.caption("Analysis Type")
                st.write(item["analysis_type"].capitalize())
                
                st.caption("Analysis Results")
                if "analysis" in item["results"]:
                    analysis = item["results"]["analysis"]
                    st.markdown(analysis)
                else:
                    st.write(item["results"])
            
            # Option to use this data again
            cols = st.columns(2)
            if item["type"] == "collect" and cols[0].button(f"Analyze This Data", key=f"analyze_{i}"):
                st.session_state.collected_data = item["results"]
                st.session_state.current_tab = "Analyze Trends"
                st.experimental_rerun()
            
            if cols[1].button(f"Export JSON", key=f"export_{i}"):
                # Create JSON string
                json_results = json.dumps(item["results"], indent=2)
                
                # Offer download
                st.download_button(
                    label="Download JSON",
                    data=json_results,
                    file_name=f"{item['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key=f"download_{i}"
                )


# Main application
def main():
    # Initialize session state
    init_session_state()
    
    # Render header
    render_header()
    
    # Render navigation tabs
    render_tabs()
    
    # Render current tab content
    if st.session_state.current_tab == "Query":
        render_query_tab()
    elif st.session_state.current_tab == "Collect Trends":
        render_collect_tab()
    elif st.session_state.current_tab == "Analyze Trends":
        render_analyze_tab()
    elif st.session_state.current_tab == "View History":
        render_history_tab()


if __name__ == "__main__":
    main()
