import argparse
from pathlib import Path
import os
from core.type_generator import TypeGenerator

def main():
    parser = argparse.ArgumentParser(description="AutoScType - Smart Contract Type Annotation Generator")
    parser.add_argument("src_dir", help="Source directory containing Solidity files")
    parser.add_argument("--output-dir", default="output", help="Output directory for generated files")
    parser.add_argument("--api-key", help="API key for LLM inference")
    parser.add_argument("--model-provider", default="deepseek", choices=["openai", "deepseek"], 
                        help="LLM provider to use (openai or deepseek)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    
    args = parser.parse_args()
    
    # Print debug information
    print("[DEBUG] CLI Arguments:")
    print(f"[DEBUG] src_dir: {args.src_dir}")
    print(f"[DEBUG] output_dir: {args.output_dir}")
    print(f"[DEBUG] api_key: {'Provided' if args.api_key else 'Not provided'}")
    print(f"[DEBUG] model_provider: {args.model_provider}")
    
    # Check if source directory/file exists
    src_path = Path(args.src_dir)
    if not os.path.exists(src_path):
        print(f"[ERROR] Source path not found: {src_path}")
        return
    
    print(f"[DEBUG] Source path exists: {src_path}")
    print(f"[DEBUG] Source path is file: {os.path.isfile(src_path)}")
    print(f"[DEBUG] Source path is directory: {os.path.isdir(src_path)}")
    
    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"[DEBUG] Output directory created: {output_path.absolute()}")
    
    # Create type generator
    generator = TypeGenerator(args.src_dir, args.api_key, args.model_provider)
    
    # Generate type files
    generator.generate_type_files(args.output_dir)
    
    # Verify output directory contents
    output_files = list(output_path.glob("*"))
    print(f"[DEBUG] Output directory contents ({len(output_files)} files):")
    for file in output_files:
        print(f"[DEBUG] - {file.name}")
    
    print(f"Type annotation files generated in {args.output_dir}/ using {args.model_provider} models")

if __name__ == "__main__":
    main() 