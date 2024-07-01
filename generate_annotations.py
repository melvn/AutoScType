import os
import sys
import openai
from pathlib import Path

# TODO: Replace with your actual OpenAI API key
openai.api_key = 'your-api-key-here'

def read_solidity_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def infer_types(content):
    prompt = """
    You are an expert in smart contract analysis and financial type systems. Your task is to analyze Solidity smart contracts and provide type annotations for variables, focusing on their financial meanings and characteristics.

    The type system stores type information for variables in the form of {numerator, denominator, normalization, and financial meaning}. The financial meanings are represented by integer keys, as follows:

    -1: "undef",
    0: "raw balance",
    1: "net balance",
    2: "accrued balance",
    3: "final balance",
    10: "compound fee ratio (t)",
    11: "transaction fee",
    12: "simple fee ratio",
    13: "transaction fee (n)",
    14: "transaction fee (d)",
    20: "simple interest ratio",
    21: "compound interest ratio",
    22: "simple interest",
    23: "compound interest",
    30: "reserve",
    40: "price/exchange rate",
    50: "debt"

    Here are some examples to help with the inference:

    1. USDCAmount, or an amount of the USDC currency, has type information {1, -1, 6, 0}:
    - 1 is a token representing USDC and is the numerator
    - -1 is a token representing nothing in the denominator
    - 6 is the base value of decimals that the USDCAmount supports (normalization)
    - 0 is the financial meaning (raw balance)

    2. WETHamount would have type information {2, -1, 18, 0}:
    - 2 is an abstract token representing WETH for the numerator
    - -1 since there is no denominator
    - 18 since WETH supports 18 decimals (normalization)
    - 0 since it is a balance

    3. feeNumerator would have type information {-1, -1, 0, 10}:
    - -1 for both numerator and denominator (no token units)
    - 0 for normalization
    - 10 for financial type (compound fee ratio)

    4. USDCToWETH would have the type information {2, 1, 12, 40}:
    - Used to convert USDC (token unit 1) to WETH (token unit 2)
    - 12 for normalization
    - 40 for financial type (price/exchange rate)

    5. USDCdecimals has type {-1, -1, 0, 6}:
    - -1 for both numerator and denominator (no token units)
    - 0 for normalization
    - 6 as it represents the number of decimals for USDC

    6. Variable nodef, which represents a constant or bool, has the type of {-1, -1, 0, -1}:
    - -1 for all fields, meaning nothing is defined

    7. For a complex struct like:
    struct Position {
        uint256 amount;
        uint256 lastUpdateTime;
    }
    Position userPosition;
    
    You might annotate it as:
    [t*], function_name, userPosition, amount, 1, -1, 18, 0
    [t*], function_name, userPosition, lastUpdateTime, -1, -1, 0, -1

    Please note:
    - Numerator and denominator types should be types of token currency (e.g., USDC, WETH, ETH, USDT).
    - These can be defined within the contract itself.
    - They should not take the value of constants. For example, if int a = 1000, it has type {-1, -1, 3, -1}, since there is no associated token currency attributed to a.
    - The normalization field typically represents the number of decimal places for the token or value.

    For the provided smart contract/s, please output the corresponding type annotations in one of the following formats:

    1. [t], function_name, variable_name
    - For variables within functions or global variables

    2. [t*], function_name, variable_name, field_name
    - For fields of variables within functions

    3. [tref], array_name
    - For entire arrays

    When analyzing the contract:
    1. Pay special attention to state variables, function parameters, and return values.
    2. Consider the context and purpose of each variable when determining its type.
    3. If a variable's type is ambiguous, provide your best guess.

    Here's the Solidity code to analyze:
    {content}

    Please output the corresponding type annotations given the above type system. Only do what is asked. No extraneous information.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a comprehensive auditor that analyzes Solidity smart contracts and provides type annotations."},
            {"role": "user", "content": prompt.format(content=content)}
        ]
    )

    return response.choices[0].message['content']

def generate_type_file(file_path, annotations):
    type_file_path = file_path.replace('.sol', '_types.txt')
    with open(type_file_path, 'w') as type_file:
        type_file.write(annotations)

def process_file(file_path):
    content = read_solidity_file(file_path)
    annotations = infer_types(content)
    generate_type_file(file_path, annotations)
    print(f"Generated type annotations for {file_path}")

def process_directory(directory_path):
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.sol'):
                file_path = os.path.join(root, file)
                process_file(file_path)

def main():
    if len(sys.argv) != 3:
        print("Usage: python generate_annotations.py <file|directory> <path>")
        sys.exit(1)

    mode = sys.argv[1]
    path = sys.argv[2]

    if mode == 'file':
        if not path.endswith('.sol'):
            print("Error: File must have a .sol extension")
            sys.exit(1)
        process_file(path)
    elif mode == 'directory':
        process_directory(path)
    else:
        print("Invalid mode. Use 'file' or 'directory'.")
        sys.exit(1)

    print("Type annotation generation complete.")

if __name__ == "__main__":
    main()