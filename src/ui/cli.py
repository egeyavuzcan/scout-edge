"""
CLI interface for Scout-Edge - AI trend tracking system.
"""
import logging
import os
import sys
import argparse
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import configuration settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Import agent
from agents.trend_agent import TrendAgent

logger = logging.getLogger(__name__)


def setup_logging():
    """Configure logging for the CLI application."""
    log_level = logging.DEBUG if config.VERBOSE_MODE else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=log_level, format=log_format)


def format_results(results: Dict[str, Any], output_format: str = "text") -> str:
    """
    Format results for CLI output.
    
    Args:
        results (Dict[str, Any]): Results to format
        output_format (str): Output format (text or json)
        
    Returns:
        str: Formatted results
    """
    if output_format == "json":
        return json.dumps(results, indent=2)
    
    # Text formatting
    output = []
    
    if "error" in results:
        output.append(f"ERROR: {results['error']}")
        return "\n".join(output)
    
    if "response" in results:
        output.append("RESPONSE:")
        output.append(results["response"])
        output.append("")
    
    if "execution_time" in results:
        output.append(f"Execution time: {results['execution_time']:.2f} seconds")
    
    if "analysis" in results:
        analysis = results["analysis"]
        output.append("\nANALYSIS:")
        if isinstance(analysis, dict) and "analysis" in analysis:
            output.append(analysis["analysis"])
        else:
            output.append(str(analysis))
    
    return "\n".join(output)


def save_results(results: Dict[str, Any], output_file: str) -> bool:
    """
    Save results to a file.
    
    Args:
        results (Dict[str, Any]): Results to save
        output_file (str): Output file path
        
    Returns:
        bool: Success status
    """
    try:
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")
        return False


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scout-Edge - AI Trend Tracking System"
    )
    
    # Command subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the trend agent")
    query_parser.add_argument("query_text", help="Query text")
    query_parser.add_argument(
        "--output", "-o", 
        default="text", 
        choices=["text", "json"],
        help="Output format"
    )
    query_parser.add_argument(
        "--save", "-s",
        default=None,
        help="Save results to file"
    )
    
    # Collect command
    collect_parser = subparsers.add_parser("collect", help="Collect trend data")
    collect_parser.add_argument(
        "--arxiv", "-a",
        default="artificial intelligence",
        help="ArXiv query"
    )
    collect_parser.add_argument(
        "--github", "-g",
        default="machine learning",
        help="GitHub query"
    )
    collect_parser.add_argument(
        "--news", "-n",
        default="AI trends",
        help="News query"
    )
    collect_parser.add_argument(
        "--max-results", "-m",
        type=int,
        default=10,
        help="Maximum results per source"
    )
    collect_parser.add_argument(
        "--output", "-o", 
        default="text", 
        choices=["text", "json"],
        help="Output format"
    )
    collect_parser.add_argument(
        "--save", "-s",
        default=None,
        help="Save results to file"
    )
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze trend data")
    analyze_parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input file with trend data"
    )
    analyze_parser.add_argument(
        "--type", "-t",
        default="comprehensive",
        choices=["brief", "comprehensive", "technical", "business"],
        help="Analysis type"
    )
    analyze_parser.add_argument(
        "--output", "-o", 
        default="text", 
        choices=["text", "json"],
        help="Output format"
    )
    analyze_parser.add_argument(
        "--save", "-s",
        default=None,
        help="Save results to file"
    )
    
    # Interactive mode
    interactive_parser = subparsers.add_parser(
        "interactive", 
        help="Start interactive session"
    )
    
    return parser.parse_args()


def handle_query(args, agent: TrendAgent):
    """Handle query command."""
    results = agent.run(args.query_text)
    
    # Print formatted results
    print(format_results(results, args.output))
    
    # Save results if requested
    if args.save:
        save_results(results, args.save)


def handle_collect(args, agent: TrendAgent):
    """Handle collect command."""
    results = agent.collect_trend_data(
        arxiv_query=args.arxiv,
        github_query=args.github,
        news_query=args.news,
        max_results=args.max_results
    )
    
    # Add timestamp
    results["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Print formatted results
    print(format_results(results, args.output))
    
    # Save results if requested
    if args.save:
        save_results(results, args.save)


def handle_analyze(args, agent: TrendAgent):
    """Handle analyze command."""
    # Load trend data from file
    try:
        with open(args.input, 'r') as f:
            trend_data = json.load(f)
    except Exception as e:
        print(f"Error loading trend data: {str(e)}")
        return
    
    # Analyze trends
    results = agent.analyze_trends(trend_data, analysis_type=args.type)
    
    # Print formatted results
    print(format_results(results, args.output))
    
    # Save results if requested
    if args.save:
        save_results(results, args.save)


def interactive_mode(agent: TrendAgent):
    """Run interactive mode."""
    print("Scout-Edge - AI Trend Tracking System")
    print("Interactive Mode (type 'exit' or 'quit' to end)")
    print("Commands:")
    print("  collect - Collect trend data")
    print("  analyze - Analyze trend data")
    print("  (any other text will be treated as a query)")
    print()
    
    while True:
        try:
            # Get user input
            user_input = input("> ")
            
            # Check for exit command
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting Scout-Edge. Goodbye!")
                break
            
            # Handle commands
            if user_input.lower() == "collect":
                # Get parameters
                arxiv_query = input("ArXiv query [artificial intelligence]: ")
                if not arxiv_query:
                    arxiv_query = "artificial intelligence"
                
                github_query = input("GitHub query [machine learning]: ")
                if not github_query:
                    github_query = "machine learning"
                
                news_query = input("News query [AI trends]: ")
                if not news_query:
                    news_query = "AI trends"
                
                max_results_str = input("Max results per source [10]: ")
                max_results = int(max_results_str) if max_results_str else 10
                
                print("Collecting trend data, please wait...")
                results = agent.collect_trend_data(
                    arxiv_query=arxiv_query,
                    github_query=github_query,
                    news_query=news_query,
                    max_results=max_results
                )
                
                print(format_results(results))
                
                # Ask if user wants to save
                save_option = input("Save results to file? (y/n): ")
                if save_option.lower() == "y":
                    filename = input("Filename [trends.json]: ")
                    if not filename:
                        filename = "trends.json"
                    save_results(results, filename)
                    
            elif user_input.lower() == "analyze":
                # Get parameters
                input_file = input("Input file with trend data: ")
                if not input_file:
                    print("No input file provided. Aborting.")
                    continue
                
                analysis_type = input(
                    "Analysis type (brief, comprehensive, technical, business) [comprehensive]: "
                )
                if not analysis_type:
                    analysis_type = "comprehensive"
                
                # Load trend data
                try:
                    with open(input_file, 'r') as f:
                        trend_data = json.load(f)
                except Exception as e:
                    print(f"Error loading trend data: {str(e)}")
                    continue
                
                print("Analyzing trends, please wait...")
                results = agent.analyze_trends(trend_data, analysis_type=analysis_type)
                
                print(format_results(results))
                
                # Ask if user wants to save
                save_option = input("Save results to file? (y/n): ")
                if save_option.lower() == "y":
                    filename = input("Filename [analysis.json]: ")
                    if not filename:
                        filename = "analysis.json"
                    save_results(results, filename)
            
            else:
                # Treat as query
                print("Processing query, please wait...")
                results = agent.run(user_input)
                print(format_results(results))
        
        except KeyboardInterrupt:
            print("\nExiting Scout-Edge. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}")


def main():
    """Main CLI entry point."""
    # Set up logging
    setup_logging()
    
    # Parse arguments
    args = parse_args()
    
    # Initialize agent
    try:
        agent = TrendAgent()
    except Exception as e:
        logger.error(f"Error initializing agent: {str(e)}")
        print(f"Error initializing agent: {str(e)}")
        return
    
    # Handle commands
    if args.command == "query":
        handle_query(args, agent)
    elif args.command == "collect":
        handle_collect(args, agent)
    elif args.command == "analyze":
        handle_analyze(args, agent)
    elif args.command == "interactive" or not args.command:
        interactive_mode(agent)
    else:
        print(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
