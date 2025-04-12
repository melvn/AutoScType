import os
import sys
import random
from datetime import datetime

# ANSI color codes for retro styling
COLORS = {
    'reset': '\033[0m',
    'bold': '\033[1m',
    'dim': '\033[2m',
    'cyan': '\033[36m',
    'magenta': '\033[35m',
    'blue': '\033[34m',
    'yellow': '\033[33m',
    'green': '\033[32m',
    'red': '\033[31m',
    'black_bg': '\033[40m',
    'red_bg': '\033[41m',
    'green_bg': '\033[42m',
    'yellow_bg': '\033[43m',
    'blue_bg': '\033[44m',
    'magenta_bg': '\033[45m',
    'cyan_bg': '\033[46m',
    'white_bg': '\033[47m',
}

# ASCII art logo for AutoScType
ASCII_LOGO = f"""
{COLORS['cyan']}╔═══════════════════════════════════════════════════════════════════════╗
║ {COLORS['yellow']}    _         _       ____       _____                               {COLORS['cyan']} ║
║ {COLORS['yellow']}   / \\  _   _| |_ ___/ ___|  ___|_   _|_   ___ __   ___             {COLORS['cyan']} ║
║ {COLORS['yellow']}  / _ \\| | | | __/ _ \\___ \\ / __|| |/ | | | / '_ \\ / _ \\            {COLORS['cyan']} ║
║ {COLORS['yellow']} / ___ \\ |_| | || (_) |__) | (__ | | | |_| | |_) |  __/            {COLORS['cyan']} ║
║ {COLORS['yellow']}/_/   \\_\\__,_|\\__\\___/____/ \\___||_|  \\__, | .__/ \\___|            {COLORS['cyan']} ║
║ {COLORS['yellow']}                                      |___/|_|                      {COLORS['cyan']} ║
║ {COLORS['magenta']}           Smart Contract Type Annotation Generator v1.0           {COLORS['cyan']} ║
╚═══════════════════════════════════════════════════════════════════════╝{COLORS['reset']}
"""

# Retro animated loading bar
def loading_bar(message="Processing", length=40, duration=0.05):
    """Display a retro-style loading bar with animation"""
    import time
    import sys
    
    chars = "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁"
    for i in range(length):
        filled = "█" * i
        empty = "▒" * (length - i)
        percentage = int((i / length) * 100)
        sys.stdout.write(f"\r{COLORS['cyan']}[{COLORS['yellow']}{filled}{COLORS['dim']}{empty}{COLORS['cyan']}] {percentage}% {COLORS['magenta']}{message} {COLORS['yellow']}{chars[i % len(chars)]}{COLORS['reset']}")
        sys.stdout.flush()
        time.sleep(duration)
    sys.stdout.write("\r" + " " * (length + len(message) + 20) + "\r")
    sys.stdout.flush()

# Function to print messages with retro styling
def print_retro(message, style='info'):
    """Print a message with retro styling based on type"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if style == 'info':
        print(f"{COLORS['cyan']}[{COLORS['yellow']}{timestamp}{COLORS['cyan']}] ► {COLORS['reset']}{message}")
    elif style == 'success':
        print(f"{COLORS['cyan']}[{COLORS['yellow']}{timestamp}{COLORS['cyan']}] {COLORS['green']}✓ {COLORS['reset']}{message}")
    elif style == 'error':
        print(f"{COLORS['cyan']}[{COLORS['yellow']}{timestamp}{COLORS['cyan']}] {COLORS['red']}✗ {COLORS['reset']}{message}")
    elif style == 'warning':
        print(f"{COLORS['cyan']}[{COLORS['yellow']}{timestamp}{COLORS['cyan']}] {COLORS['yellow']}⚠ {COLORS['reset']}{message}")
    elif style == 'debug':
        print(f"{COLORS['cyan']}[{COLORS['yellow']}{timestamp}{COLORS['cyan']}] {COLORS['dim']}◉ {COLORS['reset']}{message}")
    elif style == 'header':
        print(f"\n{COLORS['yellow']}╔{'═' * (len(message) + 2)}╗")
        print(f"║ {COLORS['cyan']}{message} {COLORS['yellow']}║")
        print(f"╚{'═' * (len(message) + 2)}╝{COLORS['reset']}\n")

# Function to display cool retro borders around text
def box_text(text, width=None):
    """Display text in a cool retro box"""
    if not width:
        width = max(len(line) for line in text.split('\n')) + 2
    
    lines = text.split('\n')
    result = [f"{COLORS['cyan']}╔{'═' * (width + 2)}╗"]
    
    for line in lines:
        padding = ' ' * (width - len(line))
        result.append(f"║ {COLORS['reset']}{line}{padding} {COLORS['cyan']}║")
    
    result.append(f"╚{'═' * (width + 2)}╝{COLORS['reset']}")
    return '\n'.join(result)

# Function to print a retro section title
def section_title(title):
    """Print a section title with retro styling"""
    print(f"\n{COLORS['cyan']}▀{'▀' * len(title)}▀")
    print(f"{COLORS['yellow']}{title}")
    print(f"{COLORS['cyan']}▄{'▄' * len(title)}▄{COLORS['reset']}\n")

# Function to show stats in a retro dashboard style
def show_stats(stats_dict):
    """Display statistics in a retro dashboard style"""
    title = "STATISTICS"
    print(f"\n{COLORS['magenta_bg']}{COLORS['yellow']} {title} {COLORS['reset']}")
    
    for key, value in stats_dict.items():
        key_formatted = f"{key}: "
        print(f"{COLORS['cyan']}{key_formatted:<20}{COLORS['yellow']}{value}{COLORS['reset']}")

# Retro progress completion message
def completion_message(task_name="Type Annotation", files_processed=1):
    """Display a retro-style completion message"""
    msg = [
        f"{COLORS['green']}╔═════════════════════════════════════════════════╗",
        f"║ {COLORS['yellow']}Task Complete: {COLORS['cyan']}{task_name:<25} {COLORS['green']}║",
        f"║ {COLORS['yellow']}Files Processed: {COLORS['cyan']}{files_processed:<22} {COLORS['green']}║",
        f"║ {COLORS['yellow']}Time: {COLORS['cyan']}{datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<29} {COLORS['green']}║",
        f"╚═════════════════════════════════════════════════╝{COLORS['reset']}"
    ]
    print("\n" + "\n".join(msg))

# Random retro quotes to display while processing
RETRO_QUOTES = [
    "Accessing mainframe...",
    "Hacking the Gibson...",
    "Running token analysis subroutine...",
    "Enhancing smart contract security...",
    "Initializing cyber protocols...",
    "Decoding blockchain data...",
    "Scanning for type inconsistencies...",
    "Applying quantum algorithms...",
    "Executing type inference matrix...",
    "Calculating token vectors...",
]

# DeepSeek pricing information (USD per 1M tokens)
PRICING = {
    'deepseek': {
        'input': {
            'standard': 0.27,  # Cache miss rate
            'discount': 0.135,  # 50% off during discount hours
        },
        'output': {
            'standard': 1.10,
            'discount': 0.550,  # 50% off during discount hours
        }
    },
    'deepseek-reasoner': {
        'input': {
            'standard': 0.55,  # Cache miss rate 
            'discount': 0.135,  # 75% off during discount hours
        },
        'output': {
            'standard': 2.19,
            'discount': 0.550,  # 75% off during discount hours
        }
    },
    'openai': {
        'input': {
            'gpt-4o': 5.00,  # Approximate rate for GPT-4o
        },
        'output': {
            'gpt-4o': 15.00,  # Approximate rate for GPT-4o
        }
    }
}

# Discount hours for DeepSeek (UTC 16:30-00:30)
def is_discount_hour():
    """Check if current time is within DeepSeek discount hours (UTC 16:30-00:30)"""
    import datetime
    # Use timezone-aware approach instead of deprecated utcnow()
    now = datetime.datetime.now(datetime.UTC)
    hour = now.hour
    minute = now.minute
    
    # Convert to minutes since midnight for easier comparison
    current_minutes = hour * 60 + minute
    discount_start = 16 * 60 + 30  # 16:30 UTC
    discount_end = 24 * 60 + 30    # 00:30 UTC next day
    
    return current_minutes >= discount_start or current_minutes <= discount_end

def estimate_api_cost(input_tokens, output_tokens, model_provider="deepseek", use_reasoner=False):
    """Estimate API usage cost based on token count and model provider"""
    if model_provider.lower() == "deepseek":
        rate_type = "discount" if is_discount_hour() else "standard"
        # Use deepseek-reasoner pricing if reasoner flag is enabled
        model_key = 'deepseek-reasoner' if use_reasoner else 'deepseek'
        discount_status = "DISCOUNT RATE" if rate_type == "discount" else "STANDARD RATE"
    elif model_provider.lower() == "openai":
        rate_type = "standard"  # OpenAI doesn't have discounted hours
        model_key = 'openai'
        model = "gpt-4o"  # Default to GPT-4o pricing
        discount_status = "STANDARD RATE"
    else:
        return "Unknown provider", 0.0
    
    # Get the appropriate pricing based on the model
    if model_key == 'openai':
        input_cost = (input_tokens / 1000000) * PRICING[model_key]['input'][model]
        output_cost = (output_tokens / 1000000) * PRICING[model_key]['output'][model]
    else:
        # Handle both deepseek and deepseek-reasoner
        input_cost = (input_tokens / 1000000) * PRICING[model_key]['input'][rate_type]
        output_cost = (output_tokens / 1000000) * PRICING[model_key]['output'][rate_type]
    
    total_cost = input_cost + output_cost
    return discount_status, total_cost

def random_quote():
    """Return a random retro quote"""
    return random.choice(RETRO_QUOTES)

# Displays a retro file banner before processing
def file_banner(filename):
    """Display a retro banner for file processing"""
    # Extract just the filename from the path
    base_filename = os.path.basename(filename)
    print(f"\n{COLORS['blue_bg']}{COLORS['yellow']} PROCESSING {base_filename} {COLORS['reset']}")
    print(f"{COLORS['cyan']}{'=' * (len(base_filename) + 12)}")
    print(f"{COLORS['yellow']}{random_quote()}{COLORS['reset']}")
    print(f"{COLORS['cyan']}{'=' * (len(base_filename) + 12)}{COLORS['reset']}\n")

# Initialize the retro UI with a clear screen and logo
def init_retro_ui():
    """Initialize the retro UI with a clear screen and logo"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(ASCII_LOGO)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{COLORS['cyan']}System initialized at {COLORS['yellow']}{current_time}{COLORS['reset']}")
    print(f"{COLORS['cyan']}{'=' * 70}{COLORS['reset']}\n")