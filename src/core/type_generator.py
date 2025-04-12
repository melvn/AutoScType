from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import json
import re
import openai
import requests
import os
import concurrent.futures

class TypeGenerator:
    def __init__(self, src_dir: str, api_key: Optional[str] = None, model_provider: str = "deepseek", use_reasoning: bool = False):
        self.src_dir = Path(src_dir)
        self.model_provider = model_provider.lower()
        self.api_key = api_key
        self.use_reasoning = use_reasoning
        
        print(f"[DEBUG] Initializing TypeGenerator with source directory: {self.src_dir}")
        print(f"[DEBUG] Source directory exists: {os.path.exists(self.src_dir)}")
        print(f"[DEBUG] Source directory is file: {os.path.isfile(self.src_dir)}")
        print(f"[DEBUG] Source directory is dir: {os.path.isdir(self.src_dir)}")
        print(f"[DEBUG] Using reasoning model: {self.use_reasoning}")
        
        # Initialize clients based on provider
        if self.model_provider == "openai" and api_key:
            self.client = openai.OpenAI(api_key=api_key)
            self.model = "gpt-4o"
            print(f"[DEBUG] Using OpenAI model: {self.model}")
        elif self.model_provider == "deepseek" and api_key:
            # Use OpenAI class for DeepSeek since they have compatible APIs
            self.client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            # Use the reasoner model if reasoning is enabled
            if self.use_reasoning:
                self.model = "deepseek-reasoner"
                print(f"[DEBUG] Using DeepSeek Reasoner model: {self.model}")
            else:
                self.model = "deepseek-chat"
                print(f"[DEBUG] Using DeepSeek Chat model: {self.model}")
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
        
        # Token usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
    
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
                temperature=0.0,  # Zero temperature for completely deterministic results
                max_tokens=8000  # Increased from 2000 to 8000 to handle larger responses
            )
            
            # Track token usage
            if hasattr(response, 'usage'):
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_output_tokens += response.usage.completion_tokens
                print(f"[DEBUG] Token usage - Input: {response.usage.prompt_tokens}, Output: {response.usage.completion_tokens}")
            
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
        
        try:
            # Extract contract elements
            # Find state variables (including visibility and type modifiers)
            variables = list(re.finditer(r"(uint|int|address)(?:\d*)?(?:\s+(?:public|private|internal))?\s+(\w+)\s*;", content))
            # Find functions (capturing name and parameters)
            functions = list(re.finditer(r"function\s+(\w+)\s*\((.*?)\)", content))
            # Find arrays (capturing name)
            arrays = list(re.finditer(r"(uint|int|address)(?:\d*)?(?:\s+(?:public|private|internal))?\s*\[\s*\]\s+(\w+)\s*;", content))
            # Find structs (capturing name and body)
            structs = list(re.finditer(r"struct\s+(\w+)\s*\{([^}]*)\}", content))
            
            # *** IMPROVED EXTERNAL CONTRACT REFERENCE DETECTION ***
            
            # Extract cross-contract references with improved patterns
            imports = list(re.finditer(r"import\s+[\"'](.+?)[\"'];", content))
            interfaces = list(re.finditer(r"interface\s+(\w+)", content))
            contracts = list(re.finditer(r"contract\s+(\w+)", content))
            
            # Extract all import statements to analyze imported contracts
            imported_contracts = []
            for imp in imports:
                import_path = imp.group(1)
                # Extract contract/interface names from import path
                last_part = import_path.split('/')[-1]
                if '.' in last_part:
                    last_part = last_part.split('.')[0]  # Remove extension
                imported_contracts.append(last_part)
                print(f"[DEBUG] Found imported contract: {last_part} from {import_path}")
            
            # ENHANCEMENT 1: IMPROVED CONTRACT VARIABLE MAPPING
            
            # Find direct contract instantiations: ContractType varName = ContractType(address)
            direct_instantiations = list(re.finditer(r"(\w+)(?:\s+(?:public|private|internal))?\s+(\w+)\s*=\s*(?:new\s+)?(\w+)\s*\(", content))
            
            # Find variable assignments: varName = ContractType(address)
            var_assignments = list(re.finditer(r"(\w+)\s*=\s*(?:new\s+)?(\w+)\s*\(", content))
            
            # Find explicit interface instantiations: IContract(address)
            interface_calls = list(re.finditer(r"(\w+)\s*\(\s*(?:address\()?(0x[a-fA-F0-9]+|[a-zA-Z0-9_]+)\s*\)", content))
            
            # Find address casts to interface types: InterfaceType(addressVar)
            address_casts = list(re.finditer(r"(\w+)\s*\(\s*([a-zA-Z0-9_]+)\s*\)", content))
            
            # Look for constant uppercase variables that are likely contract references
            contract_constants = list(re.finditer(r"(?:constant|immutable)?\s+(\w+)\s+(?:public|private|internal)?\s+([A-Z][A-Z0-9_]+)\s*=", content))
            
            # Look for address variables with uppercase names (likely contract addresses)
            address_vars = list(re.finditer(r"address(?:\s+(?:public|private|internal))?\s+([A-Z][A-Z0-9_]+)\s*;", content))
            
            # Build comprehensive interface-to-variable mapping
            interface_to_var = {}
            var_to_interface = {}
            
            # Process direct instantiations
            for inst in direct_instantiations:
                type_name = inst.group(1)  # The contract type
                var_name = inst.group(2)   # The variable name
                inst_type = inst.group(3)  # The instantiated type
                
                # Check if this is an interface type
                if type_name.startswith("I") and len(type_name) > 1 and type_name[1].isupper():
                    interface_to_var[type_name] = var_name
                    var_to_interface[var_name] = type_name
                    print(f"[DEBUG] Found direct instantiation: {var_name} → {type_name}")
                
                # Check if the instantiated type is an interface
                if inst_type.startswith("I") and len(inst_type) > 1 and inst_type[1].isupper():
                    if var_name not in var_to_interface:
                        interface_to_var[inst_type] = var_name
                        var_to_interface[var_name] = inst_type
                        print(f"[DEBUG] Found interface instantiation: {var_name} → {inst_type}")
            
            # Process variable assignments
            for assign in var_assignments:
                var_name = assign.group(1)   # The variable name
                inst_type = assign.group(2)  # The instantiated type
                
                # Check if instantiated type is an interface
                if inst_type.startswith("I") and len(inst_type) > 1 and inst_type[1].isupper():
                    if var_name not in var_to_interface:
                        interface_to_var[inst_type] = var_name
                        var_to_interface[var_name] = inst_type
                        print(f"[DEBUG] Found variable assignment: {var_name} → {inst_type}")
            
            # Process interface calls to find implicit variables
            for call in interface_calls:
                iface_name = call.group(1)  # Interface name
                
                # If this is an interface and not already mapped
                if iface_name.startswith("I") and len(iface_name) > 1 and iface_name[1].isupper():
                    # Create a variable name based on interface name but all caps
                    # e.g., IToken -> TOKEN
                    var_name = iface_name[1:].upper()
                    
                    if var_name not in var_to_interface and iface_name not in interface_to_var:
                        interface_to_var[iface_name] = var_name
                        var_to_interface[var_name] = iface_name
                        print(f"[DEBUG] Inferred variable from interface call: {var_name} → {iface_name}")
            
            # Process address variables with uppercase names
            for addr_var in address_vars:
                var_name = addr_var.group(1)
                
                # If this is an uppercase variable, it might be a contract reference
                if var_name.isupper():
                    # Try to find a matching interface
                    for iface in [i.group(1) for i in interfaces]:
                        if iface.startswith("I") and iface[1:].upper() == var_name:
                            interface_to_var[iface] = var_name
                            var_to_interface[var_name] = iface
                            print(f"[DEBUG] Matched address variable to interface: {var_name} → {iface}")
                            break
            
            # Handle common naming conventions between interfaces and implementation contracts
            # For each interface, look for a matching contract implementation
            for iface in [i.group(1) for i in interfaces]:
                if iface.startswith("I") and len(iface) > 1:
                    base_name = iface[1:]  # Remove 'I' prefix
                    # Look for matching contract implementation
                    for contract in [c.group(1) for c in contracts]:
                        if contract == base_name:
                            # The variable name is likely the uppercase version
                            var_name = base_name.upper()
                            if var_name not in var_to_interface:
                                interface_to_var[iface] = var_name
                                var_to_interface[var_name] = iface
                                print(f"[DEBUG] Inferred contract relationship: {var_name} → {iface} (from {contract})")
            
            # Fill in any missing mappings with sensible defaults
            for iface in [i.group(1) for i in interfaces]:
                if iface not in interface_to_var:
                    # Use the interface name without 'I' and capitalized as variable name
                    if iface.startswith("I") and len(iface) > 1:
                        var_name = iface[1:].upper()
                        interface_to_var[iface] = var_name
                        var_to_interface[var_name] = iface
                        print(f"[DEBUG] Applied default interface mapping: {var_name} → {iface}")
            
            # ENHANCEMENT 2: IMPROVED EXTERNAL CALL DETECTION
            
            # Find direct method calls with improved pattern
            direct_calls = list(re.finditer(r"(\w+)\.(\w+)\s*\(", content))
            
            # Find calls via interface casting: IContract(addr).function()
            interface_method_calls = list(re.finditer(r"(\w+)\s*\(\s*(?:address\()?(0x[a-fA-F0-9]+|[a-zA-Z0-9_]+)\s*\)\s*\.\s*(\w+)\s*\(", content))
            
            # Find library calls: Library.function(obj, ...)
            library_calls = list(re.finditer(r"(\w+)\.(\w+)\s*\(\s*(\w+)", content))
            
            # Find calls that use addresses directly: addr.call{value: x}(abi.encodeWithSignature("func()"))
            low_level_calls = list(re.finditer(r"(\w+)\.call\s*(?:\{\s*value\s*:\s*[^}]+\s*\})?\s*\(\s*abi\.encodeWithSignature\s*\(\s*[\"'](\w+)\(", content))
            
            # Find inherited function calls with super: super.function()
            super_calls = list(re.finditer(r"super\.(\w+)\s*\(", content))
            
            # Find common interface method calls like ERC20, ERC721
            common_interface_methods = {
                "transfer": ["IERC20", "ERC20"],
                "transferFrom": ["IERC20", "ERC20"],
                "approve": ["IERC20", "ERC20"],
                "allowance": ["IERC20", "ERC20"],
                "balanceOf": ["IERC20", "ERC20", "IERC721", "ERC721"],
                "mint": ["IERC20", "ERC20", "IERC721", "ERC721"],
                "burn": ["IERC20", "ERC20", "IERC721", "ERC721"],
                "totalSupply": ["IERC20", "ERC20"],
                "name": ["IERC20", "ERC20", "IERC721", "ERC721"],
                "symbol": ["IERC20", "ERC20", "IERC721", "ERC721"],
                "decimals": ["IERC20", "ERC20"],
                "ownerOf": ["IERC721", "ERC721"],
                "safeTransferFrom": ["IERC721", "ERC721"],
                "getApproved": ["IERC721", "ERC721"],
                "isApprovedForAll": ["IERC721", "ERC721"],
                "setApprovalForAll": ["IERC721", "ERC721"]
            }
            
            # Identify possible ERC20/ERC721 functions based on signatures
            interface_method_markers = list(re.finditer(r"function\s+(" + "|".join(common_interface_methods.keys()) + r")\s*\(", content))
            
            # Track all external calls
            ext_calls = {}
            
            # Process direct method calls
            for call in direct_calls:
                contract_var = call.group(1)
                method = call.group(2)
                
                # Skip calls on 'this' and common non-contract objects
                if contract_var in ["this", "msg", "block", "tx", "abi", "address", "type"]:
                    continue
                
                # Add to external calls
                if contract_var not in ext_calls:
                    ext_calls[contract_var] = set()
                ext_calls[contract_var].add(method)
                print(f"[DEBUG] Found direct external call: {contract_var}.{method}()")
            
            # Process interface method calls
            for call in interface_method_calls:
                interface_type = call.group(1)
                method = call.group(3)
                
                # Check if this interface has a variable mapping
                if interface_type in interface_to_var:
                    contract_var = interface_to_var[interface_type]
                else:
                    # If not, use the interface name directly
                    contract_var = interface_type
                
                # Add to external calls
                if contract_var not in ext_calls:
                    ext_calls[contract_var] = set()
                ext_calls[contract_var].add(method)
                print(f"[DEBUG] Found interface method call: {contract_var}.{method}() via {interface_type}")
            
            # Process library calls
            for call in library_calls:
                library_name = call.group(1)
                method = call.group(2)
                target_obj = call.group(3)
                
                # Skip common library objects
                if library_name in ["abi", "string", "bytes", "uint", "int", "address"]:
                    continue
                
                # Add to external calls for the library itself
                if library_name not in ext_calls:
                    ext_calls[library_name] = set()
                ext_calls[library_name].add(method)
                print(f"[DEBUG] Found library call: {library_name}.{method}({target_obj})")
            
            # Process low-level calls
            for call in low_level_calls:
                address_var = call.group(1)
                method = call.group(2)
                
                # Add to external calls
                if address_var not in ext_calls:
                    ext_calls[address_var] = set()
                ext_calls[address_var].add(method)
                print(f"[DEBUG] Found low-level call: {address_var}.call(\"function {method}()\")")
            
            # Process common interface methods
            for marker in interface_method_markers:
                method_name = marker.group(1)
                potential_interfaces = common_interface_methods[method_name]
                
                # For each potential interface
                for iface in potential_interfaces:
                    # If this interface exists in our mapped vars
                    if iface in interface_to_var:
                        contract_var = interface_to_var[iface]
                        if contract_var not in ext_calls:
                            ext_calls[contract_var] = set()
                        ext_calls[contract_var].add(method_name)
                        print(f"[DEBUG] Inferred interface method: {contract_var}.{method_name}() from {iface}")
            
            # Add any interface-specific methods found in imported interfaces
            for iface in [i.group(1) for i in interfaces]:
                # If this interface is mapped to a variable
                if iface in interface_to_var:
                    var_name = interface_to_var[iface]
                    
                    # Find all function declarations within this interface
                    interface_pattern = rf"interface\s+{iface}\s*\{{([^}}]*)\}}"
                    interface_match = re.search(interface_pattern, content, re.DOTALL)
                    
                    if interface_match:
                        interface_body = interface_match.group(1)
                        interface_functions = list(re.finditer(r"function\s+(\w+)\s*\(", interface_body))
                        
                        for func in interface_functions:
                            method_name = func.group(1)
                            if var_name not in ext_calls:
                                ext_calls[var_name] = set()
                            ext_calls[var_name].add(method_name)
                            print(f"[DEBUG] Found interface-defined method: {var_name}.{method_name}() in {iface}")
            
            # Rest of the original method...
            
            # Extract key information from imports
            import_paths = [m.group(1) for m in imports]
            interface_names = [m.group(1) for m in interfaces]
            
            # Prepare contract aliases information
            aliases = []
            for iface, var_name in interface_to_var.items():
                if iface != var_name:
                    aliases.append({"used_name": var_name, "interface_name": iface})
                    print(f"[DEBUG] Found alias: {var_name} -> {iface}")
            
            # Prepare data for the LLM
            contract_data = {
                "contractName": contract_name,
                "variables": [{"type": m.group(1), "name": m.group(2)} for m in variables],
                "functions": [{"name": m.group(1), "params": m.group(2)} for m in functions],
                "arrays": [{"type": m.group(1), "name": m.group(2)} for m in arrays],
                "structs": [],
                "imports": import_paths,
                "interfaces": interface_names,
                "contractAliases": aliases,
                "externalCalls": [{"contract": contract, "methods": list(methods)} 
                                for contract, methods in ext_calls.items()]
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
            
            # Extract function parameters and process each function in more detail
            print(f"[DEBUG] Processing {len(contract_data['functions'])} functions")
            for func_idx, func_data in enumerate(contract_data["functions"]):
                try:
                    params = []
                    func_name = func_data["name"]
                    print(f"[DEBUG] Processing function {func_idx}: {func_name}")
                    
                    # For each function, try to find the full function definition to extract more info
                    # Use a more comprehensive pattern to find function bodies
                    func_pattern = rf"function\s+{func_name}\s*\((.*?)\)(?:.*?)(?:{{|;)"
                    func_match = re.search(func_pattern, content, re.DOTALL)
                    
                    if func_match:
                        full_params = func_match.group(1)
                        # Extract typed parameters more accurately
                        for param in re.finditer(r"(\w+(?:\[\])?)(?:\s+(?:memory|storage|calldata))?\s+(\w+)", full_params):
                            param_type = param.group(1)
                            param_name = param.group(2)
                            params.append({
                                "type": param_type,
                                "name": param_name
                            })
                            print(f"[DEBUG] Found parameter {param_name} of type {param_type} in function {func_name}")
                    
                    # Add the extracted parameters to the function data
                    contract_data["functions"][func_idx]["parameters"] = params
                    
                    # Look for return type - using a more specific pattern
                    try:
                        # Create a pattern that specifically searches for the return type of this function
                        return_pattern = rf"function\s+{func_name}\s*\(.*?\).*?returns\s*\(\s*((?:\w+(?:\[\])?)(?:\s+(?:memory|storage|calldata))?)\s+(\w+)\s*\)"
                        return_match = re.search(return_pattern, content, re.DOTALL)
                        if return_match:
                            contract_data["functions"][func_idx]["return"] = {
                                "type": return_match.group(1),
                                "name": return_match.group(2)
                            }
                            print(f"[DEBUG] Found return {return_match.group(2)} of type {return_match.group(1)} in function {func_name}")
                    except Exception as e:
                        print(f"[DEBUG] Error processing return type for function {func_name}: {str(e)}")
                except Exception as e:
                    print(f"[DEBUG] Error processing function {func_idx}: {str(e)}")
                    
            # Generate annotations using a single LLM call
            if self.client:
                token_types, financial_types = self._generate_annotations_batch(contract_data, content, var_to_interface, ext_calls)
                
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
                try:
                    with open(token_file, "w") as file_handle:  # Renamed to avoid any confusion
                        file_handle.write(f"[*c], {contract_name}\n\n")
                    
                    with open(ftype_file, "w") as file_handle:  # Renamed to avoid any confusion
                        file_handle.write("")
                    print(f"[DEBUG] Created empty files with headers")
                except Exception as e:
                    print(f"[DEBUG] Error creating empty files: {str(e)}")
        except Exception as e:
            print(f"[DEBUG] Top-level error in _generate_type_annotations: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _generate_annotations_batch(self, contract_data: Dict[str, Any], content: str, var_to_interface: Dict[str, str], ext_calls: Dict[str, set]) -> Tuple[str, str]:
        """Generate both token and financial type annotations in parallel API calls."""
        
        # Common system prompt used for both annotations
        base_system_prompt = """You are an expert at analyzing Solidity smart contracts to generate precise ScType type annotations.
Your task is to create one comprehensive annotation file that follows ScType's format requirements exactly.
The annotation file must be COMPLETE and ACCURATE - missing annotations will cause type checking errors.

Pay special attention to external contract calls ([sef] and [sefa]) and skip functions ([xf]), as these
are often the most critical annotations for correct type checking."""
        
        # Define the common base user prompt that will be modified for each type
        base_user_prompt = f"""
Analyze this Solidity contract '{contract_data['contractName']}' and generate a type annotation file.

# CRITICAL GUIDELINES FOR GENERATING ACCURATE ANNOTATIONS:

1. For ALL external contract calls ([sef] and [sefa]), you MUST include ALL functions detected
   - Every single contract method call should have an annotation
   - Include all common methods like transfer, approve, balanceOf, etc.
   - Use the VARIABLE name (like "PAIRS") not the interface name (like "IPairsContract")

2. For ALL functions in the contract, consider whether they should be skipped
   - Complex functions that modify state often need [xf] annotations
   - Include ALL functions identified as external calls in the skip section if appropriate

3. Include annotations for ALL contract elements:
   - Global variables
   - Address variables (use [ta] annotations)
   - Arrays (use [tref] annotations)
   - Function parameters
   - Struct fields
   - External contract calls
   - Skip functions

## Contract Functions
Consider which of these functions should have [xf] skip annotations:
{json.dumps([f["name"] for f in contract_data["functions"]], indent=2)}

## CONTRACT INFORMATION

## Contract Name:
{contract_data['contractName']}

## Contract Aliases (Use variable names from this list in annotations):
{json.dumps(contract_data["contractAliases"], indent=2)}

## Function Parameters:
{json.dumps([{"name": f["name"], "parameters": f.get("parameters", [])} for f in contract_data["functions"]], indent=2)}

## WHAT FUNCTIONS NEED ANNOTATIONS:

## External Contract Calls
These MUST be included with [sef] and [sefa] annotations:
{json.dumps([{"contract": c, "methods": list(ext_calls.get(c, set()))} for c in var_to_interface.keys() if c in ext_calls and ext_calls[c]], indent=2)}

## All Detected External Calls
ALL of these MUST have [sef] annotations:
{json.dumps({contract: list(methods) for contract, methods in contract_data["externalCalls"]}, indent=2)}

## Full Solidity Contract:
```solidity
{content[:40000]}
```
"""

        # Token-specific system prompt - focus on token units and scaling
        token_system_prompt = base_system_prompt + """
Focus on generating a complete TOKEN TYPE file (_types.txt) that specifies token units, denominators, and scaling factors.
This file tracks the TOKEN UNITS of variables, which represent what token a variable represents (like USDC, ETH, etc).

IMPORTANT: You must include ALL annotation types as needed:
- [t] for integer variables
- [ta] for address variables
- [tref] for arrays
- [t*] for struct fields
- [sef] and [sefa] for external function calls
"""

        # Financial-specific system prompt - focus on financial meanings
        financial_system_prompt = base_system_prompt + """
Focus on generating a complete FINANCIAL TYPE file (_ftypes.txt) that specifies the financial semantic meaning of variables.
This file tracks the FINANCIAL TYPES of variables, which represent their financial purpose (balance, fee, price, etc).

IMPORTANT: You must include ALL annotation types as needed:
- [t] for integer variables with financial meaning
- [tref] for arrays with financial types
- [t*] for struct fields with financial meaning
- [sef] and [sefa] for external function calls
"""

        # Token-specific user prompt
        token_user_prompt = base_user_prompt + """
# TOKEN TYPE FILE FORMAT (_types.txt)

## 1. Required Contract Flag
`[*c], {contract_name}`

## 2. All Necessary Annotation Types

### 2.1 External Contract Annotations
`[sef], CONTRACT_VAR, function_name`
`[sefa], CONTRACT_VAR, function_name, tuple_length, {{c, num, denom, scale}}, {{c, num, denom, scale}}, ...`

### 2.2 Skip Functions (List function names without [xf] prefix)
```
addToPosition
initiateLimitOrder
cancelLimitOrder
...
```

### 2.3 Address Annotations
`[ta], {function_name}, {variable_name}, {scaling_factor}`
Example: `[ta], swap, _token0, 6` for a USDC token address

### 2.4 Array Annotations
`[tref], {variable_name}, {numerator_token_type}, {denominator_token_type}, {scaling_factor}`
Example: `[tref], balances, 1, -1, 0` for a token balance array

### 2.5 Integer Variable Annotations
`[t], {function_name}, {variable_name}, {numerator_token_type}, {denominator_token_type}, {scaling_factor}, {value}`
Examples:
- `[t], global, totalDepositCap, 1, -1, 18, [uint256]` for global variable
- `[t], deposit, _amount, 1, -1, 18, 'u'` for function parameter

### 2.6 Struct Field Annotations
`[t*], global, {struct_name}, {field_name}, {numerator_token_type}, {denominator_token_type}, {scaling_factor}, {value}`

## 3. Type Reference

#### Token Types
- Stablecoins (USDC, USDT, DAI): (1, -1, 6)
- ETH/WETH: (2, -1, 18)
- BTC/WBTC: (3, -1, 8)
- Generic tokens: (1, -1, 18)
- Non-token types: (-1, -1, 18)

## INSTRUCTIONS FOR RESPONSE:
Generate a complete and accurate TOKEN TYPE file that includes ALL necessary annotation types: [t], [ta], [tref], [t*], [sef], and [sefa].
Be thorough and don't miss any variables that need annotations, especially address variables and arrays.
RESPOND ONLY WITH THE TOKEN TYPE FILE CONTENT, NO EXPLANATIONS OR ADDITIONAL TEXT.
"""

        # Financial-specific user prompt
        financial_user_prompt = base_user_prompt + """
# FINANCIAL TYPE FILE FORMAT (_ftypes.txt)

## 1. Required Contract Flag
`[*c], {contract_name}`

## 2. All Necessary Annotation Types

### 2.1 External Contract Annotations
`[sef], CONTRACT_VAR, function_name`
`[sefa], CONTRACT_VAR, function_name, tuple_length, {{f:type}}, {{f:type}}, ...`

### 2.2 Skip Functions (WITH [xf] prefix)
```
[xf], addToPosition
[xf], initiateLimitOrder
[xf], cancelLimitOrder
...
```

### 2.3 Integer Variable Annotations
`[t], {function_name}, {variable_name}, f:{financial_type_key}`
Examples:
- `[t], global, openFees, f:10` for a fee variable
- `[t], withdraw, _amount, f:0` for a balance

### 2.4 Array Annotations
`[tref], {variable_name}, f:{financial_type_key}`
Example: `[tref], balances, f:0` for an array of balances

### 2.5 Struct Field Annotations
`[t*], global, {struct_name}, {field_name}, f:{financial_type_key}`
Example: `[t*], global, openFees, daoFees, f:10`

## 3. Financial Types Reference
- -1: undefined
- 0: raw balance (amounts, balances, shares)
- 1: net balance (staked, delegated amounts)
- 10: compound fee ratio (fees, commission rates)
- 11: transaction fee
- 12: simple fee ratio (cooldown periods)
- 20: interest ratio
- 30: reserve values
- 40: exchange rate or price
- 50: debt values
- 60: dividend/profit/reward values

## INSTRUCTIONS FOR RESPONSE:
Generate a complete and accurate FINANCIAL TYPE file that includes ALL necessary annotation types: [t], [tref], [t*], [sef], and [sefa].
Be thorough and don't miss any variables that need annotations, especially arrays with financial meaning.
RESPOND ONLY WITH THE FINANCIAL TYPE FILE CONTENT, NO EXPLANATIONS OR ADDITIONAL TEXT.
"""

        # Function to make an API call
        def make_api_call(system_prompt, user_prompt, is_financial):
            response = self._call_llm(system_prompt, user_prompt)
            if response:
                print(f"[DEBUG] {'Financial' if is_financial else 'Token'} types response received: {len(response)} characters")
                return self._process_annotation_response(response, contract_data, is_financial)
            else:
                print(f"[DEBUG] No {'financial' if is_financial else 'token'} type response received, using minimal valid output")
                return f"[*c], {contract_data['contractName']}\n\n"

        # Make API calls in parallel using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit both tasks
            token_future = executor.submit(make_api_call, token_system_prompt, token_user_prompt, False)
            financial_future = executor.submit(make_api_call, financial_system_prompt, financial_user_prompt, True)
            
            # Get results
            token_types = token_future.result()
            financial_types = financial_future.result()
            
        # ADDED DEBUG: Write full responses to debug files
        debug_dir = Path("debug")
        debug_dir.mkdir(exist_ok=True)
        try:
            with open(debug_dir / f"{contract_data['contractName']}_token_result.txt", "w") as f:
                f.write(token_types)
            with open(debug_dir / f"{contract_data['contractName']}_financial_result.txt", "w") as f:
                f.write(financial_types)
            print(f"[DEBUG] Saved processed results to debug directory")
        except Exception as e:
            print(f"[DEBUG] Failed to write debug files: {str(e)}")
            
        return token_types, financial_types
    
    def _process_annotation_response(self, response: str, contract_data: Dict[str, Any], is_financial: bool) -> str:
        """Process the LLM response for annotations and format appropriately."""
        try:
            # Check if response has the expected contract flag
            if f"[*c], {contract_data['contractName']}" not in response:
                print(f"[DEBUG] Adding missing contract flag to {'financial' if is_financial else 'token'} types")
                response = f"[*c], {contract_data['contractName']}\n\n" + response.lstrip()
            
            # Process annotations based on type
            if is_financial:
                # Ensure financial type annotations have f: prefix
                lines = response.split('\n')
                processed_lines = []
                
                for line in lines:
                    # Fix financial type annotations that are missing f: prefix
                    if "[t]," in line and not "f:" in line and not line.strip().endswith("f:"):
                        parts = line.split(',')
                        # If the last part is a number without f: prefix, add it
                        if parts[-1].strip().isdigit():
                            parts[-1] = f" f:{parts[-1].strip()}"
                            line = ','.join(parts)
                    
                    # Fix tref annotations
                    if "[tref]," in line and not "f:" in line:
                        parts = line.split(',')
                        # If the last part is a number without f: prefix, add it
                        if len(parts) >= 3 and parts[-1].strip().isdigit():
                            parts[-1] = f" f:{parts[-1].strip()}"
                            line = ','.join(parts)
                    
                    # Fix sefa annotations with proper financial type format
                    if "[sefa]" in line:
                        parts = line.split(",")
                        for i, part in enumerate(parts):
                            if "{" in part and "{{" not in part and "f:" not in part:
                                # Replace { with {{ and add f: if missing
                                parts[i] = part.replace("{", "{{").replace("}", "}}")
                                if "f:" not in parts[i]:
                                    parts[i] = parts[i].replace("}}", ", f:-1}}")
                        line = ",".join(parts)
                    
                    # Ensure proper formatting for financial type entries
                    if "f:" in line and line.strip().endswith("f:"):
                        # Fix truncated financial type entries
                        line = line.rstrip(":") + ":-1"  # Default to undefined
                    
                    processed_lines.append(line)
                
                response = '\n'.join(processed_lines)
                
                # Make sure skip functions have [xf] prefix in financial type file
                if is_financial:
                    lines = response.split('\n')
                    in_skip_section = False
                    processed_lines = []
                    
                    for i, line in enumerate(lines):
                        if line.strip() and not line.startswith('[') and not in_skip_section and i > 0 and not lines[i-1].startswith('[xf]'):
                            # This might be a skip function without prefix
                            if 'addToPosition' in line or 'withdraw' in line or 'deposit' in line or any(func["name"] in line for func in contract_data["functions"]):
                                in_skip_section = True
                                processed_lines.append(f"[xf], {line.strip()}")
                                continue
                        
                        # If we hit a section marker, we're out of skip section
                        if line.startswith('[') and line.startswith('[xf]') == False:
                            in_skip_section = False
                        
                        processed_lines.append(line)
                    
                    response = '\n'.join(processed_lines)
            else:
                # Process token type file - remove [xf] prefix from skip functions
                lines = response.split('\n')
                processed_lines = []
                skip_section = False
                
                for line in lines:
                    if line.startswith('[xf],'):
                        # Extract just the function name
                        function_name = line.split(',')[1].strip()
                        if not skip_section:
                            # Start the skip section with a blank line
                            processed_lines.append('')
                            skip_section = True
                        processed_lines.append(function_name)
                    else:
                        # Make sure we keep any existing blank line separators
                        if not line.strip() and processed_lines and processed_lines[-1].strip():
                            skip_section = False
                        processed_lines.append(line)
                
                response = '\n'.join(processed_lines)
                
                # Fix token scaling factors that look like scientific notation
                lines = response.split('\n')
                for i, line in enumerate(lines):
                    if "1e" in line and ("[t]," in line or "[ta]," in line or "[tref]," in line):
                        # Convert scientific notation like 1e18 to actual number
                        parts = line.split(',')
                        for j, part in enumerate(parts):
                            if "1e" in part:
                                try:
                                    # Extract the scientific notation part
                                    match = re.search(r'1e(\d+)', part)
                                    if match:
                                        exp = int(match.group(1))
                                        # Replace with actual number
                                        parts[j] = part.replace(f"1e{exp}", str(10**exp))
                                except:
                                    pass  # Keep original if conversion fails
                        lines[i] = ','.join(parts)
                
                response = '\n'.join(lines)
            
            # Escape any unescaped curly braces in examples to avoid f-string errors
            lines = response.split('\n')
            processed_lines = []
            
            for line in lines:
                # Safely escape any curly braces in [sefa] annotations that aren't already escaped
                if "[sefa]" in line:
                    parts = line.split(",")
                    for i, part in enumerate(parts):
                        if "{" in part and "{{" not in part:
                            # Replace { with {{ and } with }}
                            parts[i] = part.replace("{", "{{").replace("}", "}}")
                    line = ",".join(parts)
                processed_lines.append(line)
            
            return '\n'.join(processed_lines)
            
        except Exception as e:
            print(f"[DEBUG] Error processing {'financial' if is_financial else 'token'} type response: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return minimal valid output
            return f"[*c], {contract_data['contractName']}\n\n" 