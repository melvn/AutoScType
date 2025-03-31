from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import json
import re
import openai
import requests
import os

class TypeGenerator:
    def __init__(self, src_dir: str, api_key: Optional[str] = None, model_provider: str = "deepseek"):
        self.src_dir = Path(src_dir)
        self.model_provider = model_provider.lower()
        self.api_key = api_key
        
        print(f"[DEBUG] Initializing TypeGenerator with source directory: {self.src_dir}")
        print(f"[DEBUG] Source directory exists: {os.path.exists(self.src_dir)}")
        print(f"[DEBUG] Source directory is file: {os.path.isfile(self.src_dir)}")
        print(f"[DEBUG] Source directory is dir: {os.path.isdir(self.src_dir)}")
        
        # Initialize clients based on provider
        if self.model_provider == "openai" and api_key:
            self.client = openai.OpenAI(api_key=api_key)
            self.model = "gpt-4o"
            print(f"[DEBUG] Using OpenAI model: {self.model}")
        elif self.model_provider == "deepseek" and api_key:
            # Use OpenAI class for DeepSeek since they have compatible APIs
            self.client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            self.model = "deepseek-chat"
            print(f"[DEBUG] Using DeepSeek model: {self.model}")
        else:
            self.client = None
            self.model = None
            print(f"[DEBUG] No LLM client initialized. Provider: {self.model_provider}, API key provided: {bool(api_key)}")
        
        # Common ERC20 token addresses - using well-known tokens for reference only
        # This is used when a specific address is referenced in the contract
        self.token_addresses = {
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": ("USDC", 6),  # USDC
            "0xdAC17F958D2ee523a2206206994597C13D831ec7": ("USDT", 6),  # USDT
            "0x6B175474E89094C44Da98b954EedeAC495271d0F": ("DAI", 18),   # DAI
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": ("WETH", 18), # WETH
            "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": ("WBTC", 8),   # WBTC
        }
        
        # Regex patterns for token types - generic patterns applicable to any contract
        self.token_patterns = {
            # Stablecoins and USD-related tokens
            r"\b(usdc|usdt|dai|tether|usd|stable|stablecoin)\b": (1, -1, 6),
            # ETH/WETH
            r"\b(weth|eth|ether)\b": (2, -1, 18),
            # BTC/WBTC
            r"\b(wbtc|btc|bitcoin)\b": (3, -1, 8),
            # Generic token-related terms
            r"\b(token|amount|balance|value|staked|liquidity|pool|reserve|supply)\b": (1, -1, 18),
        }
        
        # Regex patterns for financial types - generic patterns applicable to any contract
        self.financial_patterns = {
            # Fee-related
            r"\bfee\b": 10,           # Compound fee ratio
            r"\bcommission\b": 10,    # Commission rate
            r"\btransactionfee\b": 11, # Transaction fee
            
            # Interest-related
            r"\binterest\b": 20,       # Simple interest ratio
            r"\bapr\b": 20,           # APR (simple interest ratio)
            r"\bapy\b": 21,           # APY (compound interest ratio)
            
            # Balance-related
            r"\bbalanceof\b": 0,      # Raw balance from balanceOf
            r"\bbalance\b": 0,        # Raw balance
            r"\bstaked\b": 1,         # Net balance
            r"\bdelegated\b": 1,      # Net balance
            r"\bamount\b": 0,         # Raw balance
            r"\bshares\b": 0,         # Raw balance
            r"\btotalshares\b": 0,    # Raw balance
            
            # Rates and prices
            r"\bexchangerate\b": 40,  # Exchange rate
            r"\brate\b": 20,          # Generic rate (default to interest)
            r"\bprice\b": 40,         # Price/exchange rate
            r"\bexchange\b": 40,      # Exchange rate
            
            # Other financial concepts
            r"\bcooldown\b": 12,      # Simple fee ratio
            r"\breward\b": 60,        # Dividend/profit
            r"\bprofit\b": 60,        # Dividend/profit
            r"\bdividend\b": 60,      # Dividend
            r"\bepoch\b": 30,         # Time period (reserve)
            r"\breserve\b": 30,       # Reserve
            r"\bdebt\b": 50,          # Debt
        }
        
        # Cache for optimized annotations
        self.annotation_cache = {}
        
        # Special annotations
        self.skip_functions = set()  # Functions to skip typechecking
        self.contract_aliases = {}   # Contract name aliases
        
        # Track token operations for composite units
        self.token_operations = {}  # Maps operation to resulting token unit
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Call LLM based on provider"""
        if not self.api_key:
            print("[DEBUG] No API key provided, skipping LLM call")
            return None
            
        print(f"[DEBUG] Calling LLM with provider: {self.model_provider}")
        try:
            # Use the OpenAI client for both providers since DeepSeek has a compatible API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Lower for more deterministic results
                max_tokens=2000  # Increased for larger responses
            )
            
            # Handle the response and extract content
            if hasattr(response, 'choices') and len(response.choices) > 0:
                result = response.choices[0].message.content.strip()
                print(f"[DEBUG] LLM response received (first 100 chars): {result[:100]}...")
                return result
            else:
                print(f"[DEBUG] Unexpected API response format: {response}")
                return None
        except Exception as e:
            print(f"[DEBUG] API request error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_type_files(self, output_dir: str):
        """Generate type annotation files for all Solidity files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"[DEBUG] Output directory created: {output_path}")
        
        # Process each Solidity file
        sol_files = list(self.src_dir.glob("**/*.sol"))
        if not sol_files:
            # Check if src_dir is a single Solidity file
            if self.src_dir.suffix == '.sol' and self.src_dir.exists():
                sol_files = [self.src_dir]
                print(f"[DEBUG] Processing single Solidity file: {self.src_dir}")
            else:
                print(f"[DEBUG] No Solidity files found in {self.src_dir} or its subdirectories")
        
        print(f"[DEBUG] Found {len(sol_files)} Solidity files")
        
        for sol_file in sol_files:
            print(f"[DEBUG] Processing Solidity file: {sol_file}")
            
            # Read the file content
            try:
                with open(sol_file) as f:
                    content = f.read()
                print(f"[DEBUG] File content length: {len(content)} characters")
            except Exception as e:
                print(f"[DEBUG] Error reading file {sol_file}: {str(e)}")
                continue
            
            # Extract contract name
            contract_match = re.search(r"contract\s+(\w+)", content)
            if not contract_match:
                print(f"[DEBUG] No contract name found in {sol_file}")
                continue
            contract_name = contract_match.group(1)
            print(f"[DEBUG] Found contract: {contract_name}")
            
            # Process the contract in a single batch
            self._generate_type_annotations(contract_name, content, output_path)
    
    def _generate_type_annotations(self, contract_name: str, content: str, output_path: Path):
        """Generate both token and financial type annotations in a single batch process."""
        token_file = output_path / f"{contract_name}_types.txt"
        ftype_file = output_path / f"{contract_name}_ftypes.txt"
        
        print(f"[DEBUG] Generating type files for {contract_name}")
        
        # Extract contract elements
        # Find state variables (including visibility and type modifiers)
        variables = list(re.finditer(r"(uint|int|address)(?:\d*)?(?:\s+(?:public|private|internal))?\s+(\w+)\s*;", content))
        # Find functions (capturing name and parameters)
        functions = list(re.finditer(r"function\s+(\w+)\s*\((.*?)\)", content))
        # Find arrays (capturing name)
        arrays = list(re.finditer(r"(uint|int|address)(?:\d*)?(?:\s+(?:public|private|internal))?\s*\[\s*\]\s+(\w+)\s*;", content))
        # Find structs (capturing name and body)
        structs = list(re.finditer(r"struct\s+(\w+)\s*\{([^}]*)\}", content))
        
        print(f"[DEBUG] Found {len(variables)} variables, {len(functions)} functions, "
              f"{len(arrays)} arrays, {len(structs)} structs")
        
        # Prepare data for the LLM
        contract_data = {
            "contractName": contract_name,
            "variables": [{"type": m.group(1), "name": m.group(2)} for m in variables],
            "functions": [{"name": m.group(1), "params": m.group(2)} for m in functions],
            "arrays": [{"type": m.group(1), "name": m.group(2)} for m in arrays],
            "structs": []
        }
        
        # Process structs and their fields
        for struct_match in structs:
            struct_name = struct_match.group(1)
            struct_fields = struct_match.group(2)
            
            struct_data = {
                "name": struct_name,
                "fields": []
            }
            
            for field in re.finditer(r"(uint|int|address)(?:\d*)?(?:\s+(?:public|private|internal))?\s+(\w+)\s*;", struct_fields):
                struct_data["fields"].append({
                    "type": field.group(1),
                    "name": field.group(2)
                })
            
            contract_data["structs"].append(struct_data)
        
        # Extract function parameters
        for func_idx, func_data in enumerate(contract_data["functions"]):
            params = []
            for param in re.finditer(r"(uint|int|address)(?:\d*)?(?:\s+(?:memory|storage|calldata))?\s+(\w+)", func_data["params"]):
                params.append({
                    "type": param.group(1),
                    "name": param.group(2)
                })
            contract_data["functions"][func_idx]["parameters"] = params
            
            # Look for return type
            return_match = re.search(r"returns\s*\(\s*((?:uint|int|address)(?:\d*)?(?:\s+(?:memory|storage|calldata))?)\s+(\w+)\s*\)", content)
            if return_match:
                contract_data["functions"][func_idx]["return"] = {
                    "type": return_match.group(1),
                    "name": return_match.group(2)
                }
        
        # Generate annotations using a single LLM call
        if self.client:
            token_types, financial_types = self._generate_annotations_batch(contract_data, content)
            
            # Write token type file
            try:
                with open(token_file, "w") as f:
                    f.write(token_types)
                print(f"[DEBUG] Token type file generated: {token_file}")
            except Exception as e:
                print(f"[DEBUG] Error writing token type file: {str(e)}")
            
            # Write financial type file
            try:
                with open(ftype_file, "w") as f:
                    f.write(financial_types)
                print(f"[DEBUG] Financial type file generated: {ftype_file}")
            except Exception as e:
                print(f"[DEBUG] Error writing financial type file: {str(e)}")
        else:
            print("[DEBUG] No LLM client available, skipping annotation generation")
            
            # Create empty files with contract header
            with open(token_file, "w") as f:
                f.write(f"[*c], {contract_name}\n\n")
            
            with open(ftype_file, "w") as f:
                f.write("")
                
    def _generate_annotations_batch(self, contract_data: Dict[str, Any], content: str) -> Tuple[str, str]:
        """Generate both token and financial type annotations in a single batch."""
        
        system_prompt = """You are an expert at analyzing Solidity smart contracts and generating precise type annotations. 
You'll be given a Solidity contract's structure and you need to generate two separate files:
1. A token type file that annotates token types 
2. A financial type file that annotates financial types

Follow the format specification exactly and output valid annotations."""
        
        # Create a comprehensive prompt that explains both types of annotations
        user_prompt = f"""
I need you to analyze this Solidity contract '{contract_data['contractName']}' and generate two separate type annotation files.

## Here's the token type annotation format:
- Start with contract flag: `[*c], {contract_data['contractName']}`
- For state variables: `[t], global, <variable_name>, <token_numerator>, <token_denominator>, <scaling_factor>, 'u'`
- For addresses: `[ta], global, <variable_name>, <token_address>`
- For arrays: `[tref], <array_name>, <token_numerator>, <token_denominator>, <scaling_factor>`
- For struct fields: `[t*], global, <struct_name>, <field_name>, <token_numerator>, <token_denominator>, <scaling_factor>, 'u'`
- For function parameters: `[t], <function_name>, <param_name>, <token_numerator>, <token_denominator>, <scaling_factor>, 'u'`
- For function returns: `[t], <function_name>, return, <token_numerator>, <token_denominator>, <scaling_factor>, 'u'`

Token types are represented as:
- Stablecoins (USDC, USDT, DAI, etc.): (1, -1, 6) for numerator 1, denominator -1, scaling factor 6
- ETH/WETH: (2, -1, 18) for numerator 2, denominator -1, scaling factor 18
- BTC/WBTC: (3, -1, 8) for numerator 3, denominator -1, scaling factor 8
- For any token-related amounts, balances, or values: (1, -1, 18) for generic tokens
- For other variables and non-token types, use (-1, -1, 18) for undefined token types

Based on the variable or parameter name, try to infer the most appropriate token type. Names containing "amount", "balance", "token", "staked", etc. are likely token-related and should use (1, -1, 18) if the specific token can't be determined.

## Here's the financial type annotation format:
- For state variables: `[t], global, <variable_name>, f:<financial_type>`
- For function parameters: `[t], <function_name>, <param_name>, f:<financial_type>`
- For function returns: `[t], <function_name>, return, f:<financial_type>`
- For struct fields: `[t*], global, <struct_name>, <field_name>, f:<financial_type>`

Financial types are numbers representing:
- -1: undefined
- 0: raw balance
- 1: net balance
- 2: accrued balance
- 3: final balance
- 10: compound fee ratio
- 11: transaction fee
- 12: simple fee ratio
- 20: simple interest ratio
- 21: compound interest ratio
- 30: reserve
- 40: price/exchange rate
- 50: debt
- 60: dividend/profit/reward

Analyze the contract carefully to infer appropriate types based on variable and function names. For example:
- Names with "fee", "commission", "rate" likely relate to fee/interest ratios
- Names with "balance", "amount", "staked" likely relate to token balances
- Names with "price", "exchange" likely relate to exchange rates
- Names with "reward", "profit" likely relate to dividends/rewards

## The contract structure:
```json
{contract_data}
```

## Full Solidity Contract:
```solidity
{content[:50000]}  # Limit to 50,000 chars to stay within context limits
```

Please output two separate type annotation files with correct formatting:

1. TOKEN_TYPE_FILE:
[Output the token type annotations here]

2. FINANCIAL_TYPE_FILE:
[Output the financial type annotations here]
"""
        
        # Make a single API call
        response = self._call_llm(system_prompt, user_prompt)
        
        if not response:
            # Return empty annotations if the API call failed
            return f"[*c], {contract_data['contractName']}\n\n", ""
        
        # Parse the response to extract the two files
        try:
            token_type_match = re.search(r"TOKEN_TYPE_FILE:\s*(.+?)(?=\n\s*\d+\.\s*FINANCIAL_TYPE_FILE:|$)", response, re.DOTALL)
            financial_type_match = re.search(r"FINANCIAL_TYPE_FILE:\s*(.+?)(?=$)", response, re.DOTALL)
            
            token_types = token_type_match.group(1).strip() if token_type_match else f"[*c], {contract_data['contractName']}\n\n"
            financial_types = financial_type_match.group(1).strip() if financial_type_match else ""
            
            # Ensure the token type file has the contract flag
            if not token_types.startswith(f"[*c], {contract_data['contractName']}"):
                token_types = f"[*c], {contract_data['contractName']}\n\n" + token_types
                
            return token_types, financial_types
        except Exception as e:
            print(f"[DEBUG] Error parsing LLM response: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return minimal valid output
            return f"[*c], {contract_data['contractName']}\n\n", "" 