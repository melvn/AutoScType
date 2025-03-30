from typing import Dict, List, Optional, Tuple
from slither import Slither
from slither.core.declarations import Contract, Function, Variable
from slither.core.solidity_types import Type, ElementaryType

class ContractParser:
    def __init__(self, src_dir: str):
        self.slither = Slither(src_dir)
        self.contracts_data = []
        self.token_addresses = {}  # Map of token addresses to their scaling factors
        
    def parse_contracts(self) -> List[Dict]:
        """Parse all contracts in the source directory."""
        for contract in self.slither.contracts:
            contract_data = {
                "name": contract.name,
                "variables": self._parse_variables(contract),
                "functions": self._parse_functions(contract),
                "token_interactions": self._detect_token_interactions(contract),
                "token_addresses": self._find_token_addresses(contract)
            }
            self.contracts_data.append(contract_data)
        return self.contracts_data
    
    def _parse_variables(self, contract: Contract) -> List[Dict]:
        """Parse contract variables with their types and metadata."""
        variables = []
        for var in contract.variables:
            var_data = {
                "name": var.name,
                "type": str(var.type),
                "visibility": var.visibility,
                "is_constant": var.is_constant,
                "is_immutable": var.is_immutable,
                "initialized": var.initialized,
                "source": contract.name,
                "is_address": isinstance(var.type, ElementaryType) and str(var.type) == "address"
            }
            variables.append(var_data)
        return variables
    
    def _parse_functions(self, contract: Contract) -> List[Dict]:
        """Parse contract functions with their parameters and return types."""
        functions = []
        for func in contract.functions:
            func_data = {
                "name": func.name,
                "parameters": [{
                    "name": param.name,
                    "type": str(param.type),
                    "is_address": isinstance(param.type, ElementaryType) and str(param.type) == "address"
                } for param in func.parameters],
                "return_type": str(func.return_type) if func.return_type else None,
                "visibility": func.visibility,
                "is_constructor": func.is_constructor,
                "is_fallback": func.is_fallback,
                "is_receive": func.is_receive,
                "source": contract.name
            }
            functions.append(func_data)
        return functions
    
    def _detect_token_interactions(self, contract: Contract) -> List[Dict]:
        """Detect ERC20 token interactions in the contract."""
        token_calls = []
        for func in contract.functions:
            for node in func.nodes:
                for call in node.internal_calls:
                    call_str = str(call).lower()
                    if any(token_call in call_str for token_call in [
                        "balanceof", "transfer", "transferfrom", "approve", "allowance"
                    ]):
                        # Try to extract token address from the call
                        token_address = self._extract_token_address(call_str)
                        token_calls.append({
                            "function": func.name,
                            "call": call_str,
                            "node": node.node_id,
                            "source": contract.name,
                            "token_address": token_address,
                            "call_type": self._get_call_type(call_str)
                        })
        return token_calls
    
    def _find_token_addresses(self, contract: Contract) -> Dict[str, int]:
        """Find token addresses and their scaling factors in the contract."""
        token_addresses = {}
        
        # Look for token address constants
        for var in contract.variables:
            if (isinstance(var.type, ElementaryType) and 
                str(var.type) == "address" and 
                var.is_constant and 
                var.initialized):
                # Check if it's a known token address
                scaling_factor = self._get_token_scaling_factor(var.name.lower())
                if scaling_factor:
                    token_addresses[var.name] = scaling_factor
        
        return token_addresses
    
    def _extract_token_address(self, call_str: str) -> Optional[str]:
        """Extract token address from a function call."""
        # TODO: Implement token address extraction from function calls
        return None
    
    def _get_call_type(self, call_str: str) -> str:
        """Determine the type of token call."""
        if "balanceof" in call_str:
            return "balanceOf"
        elif "transfer" in call_str:
            return "transfer"
        elif "transferfrom" in call_str:
            return "transferFrom"
        elif "approve" in call_str:
            return "approve"
        elif "allowance" in call_str:
            return "allowance"
        return "unknown"
    
    def _get_token_scaling_factor(self, token_name: str) -> Optional[int]:
        """Get the scaling factor for a known token."""
        token_scaling_factors = {
            "usdc": 6,
            "usdt": 6,
            "dai": 18,
            "weth": 18,
            "eth": 18,
            "wbtc": 8,
            "btc": 8
        }
        return token_scaling_factors.get(token_name)
    
    def get_contract_by_name(self, name: str) -> Optional[Dict]:
        """Get contract data by name."""
        for contract in self.contracts_data:
            if contract["name"] == name:
                return contract
        return None 