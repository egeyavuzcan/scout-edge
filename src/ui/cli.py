"""
CLI interface for Scout-Edge - AI trend tracking system.
"""
import logging
import os
import json
import argparse
from typing import Dict, Any

# Assuming config and agents are structured correctly relative to this file
from ..config import Config
from ..agents.trend_agent import TrendAgent 
from ..utils.logging_config import setup_logging

# Load configuration
config = Config()

# Configure logging for the CLI application.
setup_logging()

logger = logging.getLogger(__name__)


def format_results(results: Dict[str, Any], output_format: str = "text") -> str:
    """
    Format results for CLI output.
    
    Args:
        results (Dict[str, Any]): Results to format.
        output_format (str): Output format ('text' or 'json').
        
    Returns:
        str: Formatted results.
    """
    if output_format == "json":
        return json.dumps(results, indent=2)
    else:
        # Simple text formatting (can be enhanced)
        output = ""
        if isinstance(results, dict):
            for key, value in results.items():
                output += f"\n--- {key.replace('_', ' ').title()} ---\n"
                if isinstance(value, list):
                    if not value:
                        output += "No data found.\n"
                    for item in value:
                        if isinstance(item, dict):
                            for k, v in item.items():
                                output += f"  {k.replace('_', ' ').title()}: {v}\n"
                            output += "  ---\n"
                        else:
                            output += f"  - {item}\n"
                elif isinstance(value, str):
                    # Handle potential multi-line strings like analysis summaries
                    output += f"{value}\n"
                else:
                     output += f"{value}\n"
        else:
            output = str(results) # Fallback for non-dict results
        return output.strip()


def save_results(results: Dict[str, Any], output_file: str) -> bool:
    """
    Save results to a file.
    
    Args:
        results (Dict[str, Any]): Results to save.
        output_file (str): Output file path.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f: # Ensure UTF-8 encoding
            json.dump(results, f, indent=2, ensure_ascii=False)
        
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
    subparsers = parser.add_subparsers(dest="command", help="Command to run", required=True)

    # Interactive command
    interactive_parser = subparsers.add_parser("interactive", help="Run in interactive mode")
    
    # Query command (Example, might be removed or integrated differently)
    # query_parser = subparsers.add_parser("query", help="Query the trend agent")
    # query_parser.add_argument("query_text", help="Query text")
    
    # Collect command
    collect_parser = subparsers.add_parser("collect", help="Collect trend data from sources")
    collect_parser.add_argument("--arxiv-query", default=config.DEFAULT_QUERIES.get('arxiv', 'artificial intelligence'), help="Query for ArXiv search")
    collect_parser.add_argument("--github-query", default=config.DEFAULT_QUERIES.get('github', 'machine learning'), help="Query for GitHub search")
    collect_parser.add_argument("--news-query", default=config.DEFAULT_QUERIES.get('news', 'AI trends'), help="Query for news search (via Serper)")
    collect_parser.add_argument("--max-results", type=int, default=config.ARXIV_MAX_RESULTS, help="Maximum results per source")
    collect_parser.add_argument("-o", "--output", default="trends.json", help="Output file to save collected data (JSON format)")
    collect_parser.add_argument("--output-format", choices=["text", "json"], default="text", help="Output format for console display")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze collected trend data using LLM")
    analyze_parser.add_argument("input", help="Input JSON file containing collected trend data")
    analyze_parser.add_argument("--type", choices=["brief", "comprehensive", "technical", "business"], default="comprehensive", help="Type of analysis to perform")
    analyze_parser.add_argument("-s", "--save", help="Output file to save analysis results (JSON format)")
    analyze_parser.add_argument("--output-format", choices=["text", "json"], default="text", help="Output format for console display")
    
    return parser.parse_args()

# Example handler (might be removed or adapted)
# def handle_query(args, agent: TrendAgent):
#     """Handle query command."""
#     logger.info(f"Executing query: {args.query_text}")
#     response = agent.run(args.query_text)
#     print("\nAgent Response:")
#     print(format_results(response, output_format="text"))

def handle_collect(args, agent: TrendAgent):
    """Handle collect command."""
    logger.info(f"Collecting trend data...")
    logger.info(f" ArXiv Query: '{args.arxiv_query}'")
    logger.info(f" GitHub Query: '{args.github_query}'")
    logger.info(f" News Query: '{args.news_query}'")
    logger.info(f" Max Results: {args.max_results}")
    
    results = agent.collect_trend_data(
        arxiv_query=args.arxiv_query,
        github_query=args.github_query,
        news_query=args.news_query,
        max_results=args.max_results
    )
    
    print("\nCollection Results:")
    print(format_results(results, args.output_format))
    
    if args.output:
        save_results(results, args.output)

def handle_analyze(args, agent: TrendAgent):
    """Handle analyze command."""
    logger.info(f"Analyzing trends from {args.input} (type: {args.type})...")
    try:
        with open(args.input, 'r', encoding='utf-8') as f: # Ensure UTF-8 encoding
            trend_data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Input file not found: {args.input}")
        return
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON format in file: {args.input}")
        return
    except Exception as e:
        print(f"ERROR: Error loading trend data from {args.input}: {e}")
        return

    results = agent.analyze_trends(trend_data, analysis_type=args.type)
    
    # Check for error in results
    if isinstance(results, dict) and 'error' in results:
        print(f"\nERROR during analysis: {results['error']}")
    else:
        print("\nAnalysis Results:")
        print(format_results(results, args.output_format))
        
        if args.save:
            if isinstance(results, dict):
                save_results(results, args.save)
            else:
                # Handle cases where analysis might return a plain string (though ideally it shouldn't)
                try:
                    save_results({"analysis_summary": str(results)}, args.save) 
                except Exception as e:
                    print(f"ERROR: Could not save non-dictionary analysis result: {e}")

def interactive_mode(agent: TrendAgent):
    """Run interactive mode."""
    print("Scout-Edge - AI Trend Tracking System")
    print("Interactive Mode (type 'exit' or 'quit' to end)")
    print("Commands:")
    print("  collect - Collect trend data")
    print("  analyze - Analyze trend data")
    # print("  (any other text will be treated as a query)") # Querying needs refinement

    while True:
        try:
            user_input = input("\n> ").strip().lower()
            if user_input in ["exit", "quit"]:
                break
            
            if user_input == "collect":
                # Get parameters interactively
                arxiv_query = input(f"ArXiv query [{config.DEFAULT_QUERIES.get('arxiv', 'artificial intelligence')}]: ").strip() or config.DEFAULT_QUERIES.get('arxiv', 'artificial intelligence')
                github_query = input(f"GitHub query [{config.DEFAULT_QUERIES.get('github', 'machine learning')}]: ").strip() or config.DEFAULT_QUERIES.get('github', 'machine learning')
                news_query = input(f"News query [{config.DEFAULT_QUERIES.get('news', 'AI trends')}]: ").strip() or config.DEFAULT_QUERIES.get('news', 'AI trends')
                max_results_str = input(f"Max results per source [{config.ARXIV_MAX_RESULTS}]: ").strip()
                max_results = int(max_results_str) if max_results_str.isdigit() else config.ARXIV_MAX_RESULTS

                print("\nCollecting trend data, please wait...")
                results = agent.collect_trend_data(
                    arxiv_query=arxiv_query, 
                    github_query=github_query, 
                    news_query=news_query,
                    max_results=max_results
                )
                print("\nCollection Results:")
                print(format_results(results))
                
                save = input("\nSave results to file? (y/n): ").lower()
                if save == 'y':
                    default_filename = "trends.json"
                    filename = input(f"Filename [{default_filename}]: ").strip() or default_filename
                    save_results(results, filename)
                    
            elif user_input == "analyze":
                input_file = input("Input file with trend data: ").strip()
                if not input_file:
                     print("ERROR: Input file path cannot be empty.")
                     continue
                if not os.path.exists(input_file):
                    print(f"ERROR: File not found: {input_file}")
                    continue
                
                analysis_type = input("Analysis type (brief, comprehensive, technical, business) [comprehensive]: ").strip().lower() or "comprehensive"
                
                print("\nAnalyzing trends, please wait...")
                try:
                    with open(input_file, 'r', encoding='utf-8') as f: # Ensure UTF-8 encoding
                        trend_data = json.load(f)
                except FileNotFoundError:
                    print(f"ERROR: Input file not found: {input_file}")
                    continue
                except json.JSONDecodeError:
                    print(f"ERROR: Invalid JSON format in file: {input_file}")
                    continue
                except Exception as e:
                    print(f"ERROR: Error loading trend data from {input_file}: {e}")
                    continue
                    
                results = agent.analyze_trends(trend_data, analysis_type=analysis_type)
                
                # Check for error in analysis results
                if isinstance(results, dict) and 'error' in results:
                    print(f"\nERROR during analysis: {results['error']}")
                else:
                    print("\nAnalysis Results:")
                    print(format_results(results))
                    
                    save = input("\nSave analysis results to file? (y/n): ").lower()
                    if save == 'y':
                        default_filename = "analysis.json"
                        filename = input(f"Filename [{default_filename}]: ").strip() or default_filename
                        if isinstance(results, dict):
                           save_results(results, filename)
                        else:
                            # Handle cases where analysis might return a plain string
                            try:
                                save_results({"analysis_summary": str(results)}, filename)
                            except Exception as e:
                                print(f"ERROR: Could not save non-dictionary analysis result: {e}")
                                
            # elif user_input: # Basic query handling needs refinement
            #     print("\nProcessing query...")
            #     response = agent.run(user_input)
            #     print("\nAgent Response:")
            #     print(format_results(response))
            else:
                print("Unknown command. Available commands: collect, analyze, exit, quit")
                
        except KeyboardInterrupt:
            print("\nExiting interactive mode.")
            break
        except EOFError: # Handle Ctrl+D or abrupt termination
             print("\nExiting interactive mode due to EOF.")
             break
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            logger.error(f"Interactive mode error: {e}", exc_info=True)

    print("Exiting Scout-Edge. Goodbye!")


def main():
    """Main CLI entry point."""
    args = parse_args()
    
    # Initialize the main agent
    try:
        agent = TrendAgent(config=config)
    except Exception as e:
        logger.error(f"Failed to initialize TrendAgent: {e}", exc_info=True)
        print(f"ERROR: Failed to initialize the application agent. Check configuration and API keys. Error: {e}")
        return # Exit if agent cannot be initialized

    if args.command == "interactive":
        interactive_mode(agent)
    # elif args.command == "query":
    #     handle_query(args, agent)
    elif args.command == "collect":
        handle_collect(args, agent)
    elif args.command == "analyze":
        handle_analyze(args, agent)
    else:
        # This should not happen due to 'required=True' in subparsers, but good practice
        logger.error(f"Unknown command: {args.command}")
        print(f"Error: Unknown command '{args.command}'. Use --help for options.")


if __name__ == "__main__":
    main()
