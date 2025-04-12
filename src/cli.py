import argparse
from pathlib import Path
import os
from core.type_generator import TypeGenerator
# Fix imports for the retro CLI
try:
    from utils.retro_cli import *
except ImportError:
    # Fallback to direct import if utils is not a proper package
    import sys
    import os.path
    sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
    from retro_cli import *
import time

def main():
    # Initialize our retro UI
    init_retro_ui()
    
    parser = argparse.ArgumentParser(description="AutoScType - Smart Contract Type Annotation Generator")
    parser.add_argument("src_dir", help="Source directory containing Solidity files")
    parser.add_argument("--output-dir", default="output", help="Output directory for generated files")
    parser.add_argument("--api-key", help="API key for LLM inference")
    parser.add_argument("--model-provider", default="deepseek", choices=["openai", "deepseek"], 
                        help="LLM provider to use (openai or deepseek)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--reasoning", action="store_true", help="Enable reasoning model (R1) to improve annotation quality")
    
    args = parser.parse_args()
    
    # Print debug information with retro styling
    section_title("CLI ARGUMENTS")
    print_retro(f"src_dir: {args.src_dir}", "debug")
    print_retro(f"output_dir: {args.output_dir}", "debug")
    print_retro(f"api_key: {'Provided' if args.api_key else 'Not provided'}", "debug")
    print_retro(f"model_provider: {args.model_provider}", "debug")
    print_retro(f"reasoning: {args.reasoning}", "debug")
    
    # Check if source directory/file exists
    src_path = Path(args.src_dir)
    if not os.path.exists(src_path):
        print_retro(f"Source path not found: {src_path}", "error")
        return
    
    print_retro(f"Source path exists: {src_path}", "debug")
    print_retro(f"Source path is file: {os.path.isfile(src_path)}", "debug")
    print_retro(f"Source path is directory: {os.path.isdir(src_path)}", "debug")
    
    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    print_retro(f"Output directory created: {output_path.absolute()}", "debug")
    
    # Create type generator with retro loading animation
    loading_bar("Initializing Type Generator", 30, 0.02)
    
    generator = TypeGenerator(args.src_dir, args.api_key, args.model_provider, args.reasoning)
    
    # Generate type files with retro styling
    section_title("GENERATING TYPE FILES")
    print_retro("Starting type annotation generation...", "info")
    
    start_time = time.time()
    generator.generate_type_files(args.output_dir)
    elapsed_time = time.time() - start_time
    
    # Verify output directory contents
    output_files = list(output_path.glob("*"))
    
    # Calculate cost estimation if tokens were tracked
    cost_status = "N/A"
    cost_estimate = 0.0
    
    if hasattr(generator, 'total_input_tokens') and hasattr(generator, 'total_output_tokens'):
        input_tokens = generator.total_input_tokens
        output_tokens = generator.total_output_tokens
        
        if input_tokens > 0 or output_tokens > 0:
            cost_status, cost_estimate = estimate_api_cost(
                input_tokens, 
                output_tokens, 
                args.model_provider,
                args.reasoning
            )
    
    stats = {
        "Files Generated": len(output_files),
        "Elapsed Time": f"{elapsed_time:.2f} seconds",
        "Model Provider": args.model_provider,
        "Reasoning Model": "Enabled" if args.reasoning else "Disabled",
        "Input Tokens": f"{generator.total_input_tokens:,}",
        "Output Tokens": f"{generator.total_output_tokens:,}",
        "Cost Estimate": f"${cost_estimate:.4f} ({cost_status})"
    }
    
    show_stats(stats)
    
    print_retro("Output directory contents:", "debug")
    for file in output_files:
        print_retro(f"- {file.name}", "debug")
    
    # Final success message
    completion_message("Type Annotation Generation", len(output_files))
    print_retro(f"Type annotation files generated in {args.output_dir}/ using {args.model_provider} models", "success")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_retro("\nOperation cancelled by user", "warning")
    except Exception as e:
        print_retro(f"An error occurred: {str(e)}", "error") 