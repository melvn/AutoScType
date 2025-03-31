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