# AutoScType

AutoScType is a Solidity smart contract type annotation generator that uses AI to analyze contracts and generate precise type annotations for token and financial types.

## Features

- **Batch Processing**: Efficiently processes entire Solidity contracts in a single API call
- **Dual Annotation Types**: Generates both token type and financial type annotations
- **Multiple Model Support**: Compatible with both OpenAI and DeepSeek AI models
- **Intelligent Inference**: Infers token and financial types based on naming patterns and semantics
- **Generic Compatibility**: Works with any Ethereum/Solidity smart contract

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AutoScType.git
   cd AutoScType
   ```

2. Install required dependencies:
   ```bash
   pip install openai requests
   ```

## Usage

```bash
python src/cli.py <solidity_file_or_directory> --output-dir <output_directory> --api-key <your_api_key> [--model-provider <openai|deepseek>]
```

### Arguments

- `<solidity_file_or_directory>`: Path to a Solidity file or directory containing Solidity files
- `--output-dir`: Directory where annotation files will be saved (default: "output")
- `--api-key`: Your API key for OpenAI or DeepSeek
- `--model-provider`: AI model provider to use (options: "openai" or "deepseek", default: "deepseek")
- `--debug`: Enable debug output

### Example

```bash
python src/cli.py contracts/MyToken.sol --output-dir outputs --api-key sk-your-api-key-here --model-provider deepseek
```

## Output Files

For each Solidity contract, AutoScType generates two annotation files:

1. `<ContractName>_types.txt`: Token type annotations
2. `<ContractName>_ftypes.txt`: Financial type annotations

### Token Type Format

- Contract flag: `[*c], <contract_name>`
- State variables: `[t], global, <variable_name>, <token_numerator>, <token_denominator>, <scaling_factor>, 'u'`
- Addresses: `[ta], global, <variable_name>, <token_address>`
- Arrays: `[tref], <array_name>, <token_numerator>, <token_denominator>, <scaling_factor>`
- Struct fields: `[t*], global, <struct_name>, <field_name>, <token_numerator>, <token_denominator>, <scaling_factor>, 'u'`
- Function parameters: `[t], <function_name>, <param_name>, <token_numerator>, <token_denominator>, <scaling_factor>, 'u'`
- Function returns: `[t], <function_name>, return, <token_numerator>, <token_denominator>, <scaling_factor>, 'u'`

#### Token Types

- Stablecoins (USDC, USDT, DAI): (1, -1, 6)
- ETH/WETH: (2, -1, 18)
- BTC/WBTC: (3, -1, 8)
- Generic tokens: (1, -1, 18)
- Non-token types: (-1, -1, 18)

### Financial Type Format

- State variables: `[t], global, <variable_name>, f:<financial_type>`
- Function parameters: `[t], <function_name>, <param_name>, f:<financial_type>`
- Function returns: `[t], <function_name>, return, f:<financial_type>`
- Struct fields: `[t*], global, <struct_name>, <field_name>, f:<financial_type>`

#### Financial Types

- `-1`: undefined
- `0`: raw balance
- `1`: net balance
- `2`: accrued balance
- `3`: final balance
- `10`: compound fee ratio
- `11`: transaction fee
- `12`: simple fee ratio
- `20`: simple interest ratio
- `21`: compound interest ratio
- `30`: reserve
- `40`: price/exchange rate
- `50`: debt
- `60`: dividend/profit/reward

## How It Works

1. **Contract Parsing**: AutoScType analyzes the Solidity contract to extract variables, functions, structs, and their relationships.
2. **Data Preparation**: The extracted contract elements are structured in a format suitable for AI analysis.
3. **Batch Processing**: Instead of making multiple API calls, the entire contract is processed in a single AI inference request.
4. **Type Inference**: The AI model analyzes patterns in variable and function names to determine appropriate types.
5. **File Generation**: The inferred types are formatted according to the specified annotation formats and saved to output files.

## Design Philosophy

AutoScType is designed with the following principles:

- **Efficiency**: Minimize API calls and processing time by using batch processing
- **Context Awareness**: Analyze the entire contract to make more informed type decisions
- **Flexibility**: Support multiple AI providers and adapt to different contract patterns
- **Generality**: Work with any Ethereum smart contract, not just specific token types

## Troubleshooting

- **Empty Output Files**: Ensure your API key is valid and the rate limits haven't been exceeded
- **API Errors**: Check the debug output for specific error messages from the AI provider
- **Parsing Errors**: Make sure your Solidity contract is syntactically correct
- **Missing Annotations**: If specific annotations are missing, consider adjusting the prompt or manually adding them

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

# Purpose

ScType2 is an upgraded version of the original static analysis tool written in Python3 to detect accounting errors in Solidity smart contracts. The original work can be found at [Github](https://github.com/NioTheFirst/ScType).

## Documentation 

ScType leverages the single-static-assignment representation produced by [Slither](https://github.com/crytic/slither) to perform abstract type inference. It assigns initial abstract types to select variables based on a type file or inference from the code. Then, the abstract types are propogated throughout the contract based on the produced representation and typechecked accordingly.

ScType checks each individual function within the code. Users are able to specify the abstract types of the initial function parameters through the type file, however the majority of abstract type assignment to variables is done through propogation. 

ScType can handle simple variables as well as arrays and object fields. It can also handle function calls as long as the function is located within the user-defined scope. This includes calls to functions outside of the current file being checked. See the section "Build and Run from Source Code" for more information on usage and scope.

In the following sections, we describe how to pull a Docker image for ScType, and how to reproduce the key results from our paper using the image.

## Automatic Type Annotation

ScType2 now includes an automatic type annotation feature that uses GPT-4o to infer types for variables in Solidity smart contracts. This feature can significantly reduce the manual effort required to create type files. In the original ICSE2024 Paper by Brian Zhang under Section 4.1 it is noted that future work can be done to automatically infer types through mining or, in this case, using the semantic reasoning ability of Large Language Models to cheaply and efficently mine the financial types through solidity source code alone.

### How it works

1. The tool analyzes the Solidity code using deepseek-chat.
2. It generates type annotations for variables, focusing on their financial meanings and characteristics.
3. The generated annotations are used alongside any existing manual annotations.

### Using the Automatic Type Annotation

To use the automatic type annotation feature:

1. Ensure you have set up your OpenAI API key in the `generate_annotations.py` file.

2. Run the annotation generator:
For a single file:  `python src/cli.py pathtoyourcontracts --output-dir nameofyouroutputfolder --api-key`

For a directory: `python src/cli.py pathtoyourcontracts --output-dir nameofyouroutputfolder --api-key`

3. The tool will generate two files for each processed Solidity file:
   - `{contract_name}_types.txt`: Contains token type annotations
   - `{contract_name}_ftypes.txt`: Contains finance type annotations
   These files will be placed in the same directory as the corresponding Solidity file.

Note: While the automatic annotation feature will significantly reduce manual work, it's recommended to review and potentially adjust the generated annotations for critical contracts.

<br>

The Docker Image requires 24GB of space.

ScType is applying for:

1. Available. ScType is publically available on [Github](https://github.com/NioTheFirst/ScType). We have also provided a runnable image of the tool on [Dockerhub](https://hub.docker.com/repository/docker/icse24sctype/full/general) and provide instructions to pull and run below.

2. Reusable. We provide detailed instructions on how to reproduce the results in the paper. We also provide an explanation of key components of ScType and how developers can leverage our tool in the file [`README_dev.md`](XXX) in this directory.
Finally, ScType is built on top of Slither, a well-known open-source project. Using open-source code improves reusability by making the code easier to understand.

# Provenance

ScType is publically available in this repository on [Github](https://github.com/NioTheFirst/ScType), and a runnable docker image of the tool can be found on [Dockerhub](https://hub.docker.com/repository/docker/icse24sctype/full/general). Please refer to the "Setup" section for more details.

The DOI for this repository on Zenodo is provided below:

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10449162.svg)](https://doi.org/10.5281/zenodo.10449162)

The pre-print for the corresponding paper to this artifact, _Towards Finding Accounting Errors in Smart Contracts_, can be found in this repository. For convenience, the [link](https://github.com/NioTheFirst/ScType/blob/main/icse2024-paper1049.pdf) is provided.

# Setup

The following subsections detail how to pull the Docker image and how to understand the output of the artifact.

## Pulling the Docker Image

Docker needs to be installed in order to pull the image. It can be installed [here](https://docs.docker.com/engine/install/). 

To pull the [Dockerhub](https://hub.docker.com/r/icse24sctype/full) image for ScType, ensure there is at least 24 GB of storage available and run the following command:

`docker pull icse24sctype/full:latest`

The pull should take around 40 minutes to finish.

To run the image as a container, run the following command:

`docker run -it icse24sctype/full`

Doing so should create an interactable shell. __Commands in the "Usage" section below should be run inside that shell__.

## Understanding ScType Output

For each project, ScType will output warnings corresponding to code impacted by an erroneous accounting bug.

Individual warnings are output with green text with the following format: 

`>typecheck error: Var name: A Func name: B in C`

This warning means that the intermediate representation (IR) variable "A" located within function with name "B" is incorrect, and the problematic operation or declaration is within IR expression "C".

The number of functions checked are reported in the following format:

`>Function count: XXX`

The number of annotations are reported in the following format:

`>Annotation count: XXX`

Please note that some outputs will contain more than one set of `Annotation count` and `Function count`. This is due to ScType checking more than one file. In such a scenario, disregard all but the last pair of `Annotation count` and `Function count` in a singular ScType execution.

The total number of warnings reported by the tool are reported in the following line in the following format:

`>XXX analyzed ... XXX result(s) found`

__This line represents the end of a singular ScType execution. For certain projects, ScType is run more than once.__

The total expected warnings from all ScType executions for each project are reported in the line starting with "[*]":

`>[*] Expected XXX warnings for XXX `

The total execution time of all ScType executions is reported in the following format:

`>Elapsed time: XXX.XXX seconds`



# Usage

The following subsections detail a basic usage command to test the artifact docker image installation, and how to reproduce the major results in our paper.

## Basic Usage Command

In order to test the installation of the image, please run the following command within the interactable shell produced by the Docker Image. 

`./test_benchmark_final.sh 1`

Refer to the "Setup" section for instructions on how to download the Docker Image and produce the interactable shell.

The output of the command should look like the following screenshot:

![Expected Results of MarginSwap](https://github.com/NioTheFirst/ScType/blob/main/Expected_results_marginswap.png)

This output is produced by running ScType against the first smart contract project in our dataset, MarginSwap. 

## Dataset Evaluation

To run ScType against the entire dataset, run the following command within the interactable shell:

`./test_benchmark_final.sh`

The entire execution will take 10 minutes.

The expected results of the batch execution can be found in `expected_output.txt`.

To run ScType against individual projects in the dataset, append the index of the project to the previous command.

For example, Vader Protocol p1 is the 2nd project. Hence, to only run ScType against it, input the following command:

`./test_benchmark_final.sh 2`

Individual results are found in the `run_results` repository. See the `README.md` file within for more information.

For most test cases, the number of identified true positives will be less than the reported warnings. This is due to the propogation of a single accounting error throughout multiple operations within the contract. 

For a small number of examples, the number of reported warnings may differ by a slight amount from the number of reported number of warnings in the paper, `expected_output.txt` file, and the `run_results` repository. This is due to the order of certain underlying single-static-assignment representations generated by Slither being inconsistent, in particular for Phi propagation representations. 

We briefly go over the reproduceable results in the paper as follows.

### Table 3: Evaluation Results

The data from table 3 on page 8 of our [paper](https://github.com/NioTheFirst/ScType/blob/main/icse2024-paper1049.pdf) was obtained by running ScType against the entire dataset: 

The number of annotations was obtained through the metric defined in the "Type File Parsing" section of the file [`README-dev.md`](XXX), which can be found in this directory. It can be compared to the `Annotation count` output.

The number of functions checked can be compared to the `Function count` output.

For projects 15, 17, and 19, ScType was run more than once. In this case, the number of annotations and number of function checked was obtained by adding the annotations and function checked for each execution. Please refer to the "Understanding ScType Output" subsection for more details on how to identify the end of an ScType execution.

The reported number of warnings is directly the amount reported by the tool.

The number of true positives, false positives, missed-type-errors and not-type-errors were determined by manual inspection of the warnings. The expected results and distribution of true and false positives can be found in the `run_results` directory. 
See the `README.md` file within for more details.

The execution time of the tool was obtained by using a clock within the testing scripts. It can be compared to the `Elapsed time` output.

## Reasoning Model (R1)

The reasoning model uses DeepSeek's R1 model to improve annotation quality:

- **How it works**: When enabled, AutoScType uses DeepSeek's R1 model instead of the standard DeepSeek Chat model.
- **When to use it**: Enable this feature when you need higher quality annotations, especially for complex contracts.
- **Benefits**:
  - Improves annotation completeness and accuracy
  - Enhanced reasoning capabilities for complex financial relationships
  - Better at determining token semantics and financial types
  - Particularly effective when dealing with complex contracts
- **Usage**: Add the `--reasoning` flag to your command when running AutoScType

The reasoning model has higher pricing than the standard model but provides significantly better results. During discount hours (UTC 16:30-00:30), the price difference is minimal due to higher discount rates for the reasoning model.
