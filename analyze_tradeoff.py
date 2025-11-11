import sys
import os
import time
import subprocess
import hashlib
import pandas as pd
import matplotlib.pyplot as plt

# --- Configuration ---
# Adjust these parameters for your experiment

PYTHON_CMD = sys.executable  # Use the current python executable
GEN_SCRIPT = "rainbowgen.py"
CRACK_SCRIPT = "rainbowcrack.py"

# Parameters to keep constant for a fair test
ALGORITHM = "sha1"
CHARSET = "alphanumeric"
MIN_LEN = 1
MAX_LEN = 6  # Max length for the password
CHAIN_LEN = 200

# The "variable" we are testing: Number of chains
# More chains = More memory (file size)
# We will test each of these values
N_CHAINS_LIST = [1000, 5000, 10000, 20000, 40000]

# The target password and hash to find
# Must match the constant parameters (e.g., "ab1" is alphanumeric, length 3)
TARGET_PASSWORD = "ab1"
TARGET_HASH = hashlib.sha1(TARGET_PASSWORD.encode('utf-8')).hexdigest()

# --- End Configuration ---


def run_experiment():
    """
    Runs the full experiment and returns a list of results.
    """
    results = []
    
    print(f"Starting experiment...")
    print(f"Target Hash: {TARGET_HASH} (for password '{TARGET_PASSWORD}')\n")

    for n_chains in N_CHAINS_LIST:
        print(f"--- Testing with n_chains = {n_chains} ---")
        
        output_file = f"temp_table_{n_chains}.rt"
        
        # 1. Measure Generation Time
        gen_command = [
            PYTHON_CMD, GEN_SCRIPT,
            ALGORITHM, CHARSET,
            str(MIN_LEN), str(MAX_LEN),
            str(CHAIN_LEN), str(n_chains),
            output_file
        ]
        
        print("Running rainbowgen.py...")
        start_time = time.perf_counter()
        # We capture output to hide the script's own logs for a cleaner report
        subprocess.run(gen_command, check=True, capture_output=True)
        end_time = time.perf_counter()
        gen_time_s = end_time - start_time
        print(f"Generation took: {gen_time_s:.2f} s")

        # 2. Measure File Size (Memory)
        file_size_bytes = os.path.getsize(output_file)
        file_size_kb = file_size_bytes / 1024
        print(f"File size: {file_size_kb:.2f} KB")

        # 3. Measure Cracking Time
        crack_command = [
            PYTHON_CMD, CRACK_SCRIPT,
            TARGET_HASH,
            output_file
        ]
        
        print("Running rainbowcrack.py...")
        start_time = time.perf_counter()
        # Run 5 times and take the average for a more stable crack time
        crack_times = []
        for _ in range(5):
            proc_start = time.perf_counter()
            subprocess.run(crack_command, check=True, capture_output=True)
            proc_end = time.perf_counter()
            crack_times.append(proc_end - proc_start)
        
        crack_time_s = sum(crack_times) / len(crack_times)
        print(f"Cracking took (avg of 5): {crack_time_s:.4f} s")

        # 4. Store results
        results.append({
            "Chains": n_chains,
            "File Size (KB)": file_size_kb,
            "Generation Time (s)": gen_time_s,
            "Cracking Time (s)": crack_time_s,
        })
        
        print("\n")

    return results

def analyze_and_plot(results):
    """
    Generates a table and plots from the results.
    """
    if not results:
        print("No results to analyze.")
        return
        
    # 1. Create Pandas DataFrame for the table
    df = pd.DataFrame(results)
    
    # 2. Print the final report table (in markdown format)
    print("\n--- Experiment Summary ---")
    print(df.to_markdown(index=False, floatfmt=".4f"))

    # 3. Create Plots
    
    # Plot 1: Generation Cost (Time & Size)
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    color = 'tab:red'
    ax1.set_xlabel('Number of Chains (Table Size)')
    ax1.set_ylabel('Generation Time (s)', color=color)
    ax1.plot(df['Chains'], df['Generation Time (s)'], 'o-', color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    color = 'tab:blue'
    ax2.set_ylabel('File Size (KB)', color=color)
    ax2.plot(df['Chains'], df['File Size (KB)'], 's--', color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # so the right y-label is not clipped
    plt.title('Generation Cost (Time and Memory)')
    plt.grid(True)
    plt.savefig('generation_cost_plot.png')
    print("\nSaved plot: 'generation_cost_plot.png'")

    # Plot 2: The Time-Memory Trade-off (Cracking Time)
    plt.figure(figsize=(10, 6))
    plt.plot(df['File Size (KB)'], df['Cracking Time (s)'], 'o-')
    plt.xlabel('File Size (KB)  <--- (Memory Cost)')
    plt.ylabel('Cracking Time (s)  <--- (Time Cost)')
    plt.title('Time-Memory Trade-off')
    plt.grid(True)
    plt.savefig('tradeoff_plot.png')
    print("Saved plot: 'tradeoff_plot.png'")


if __name__ == "__main__":
    try:
        experiment_results = run_experiment()
        analyze_and_plot(experiment_results)
    except FileNotFoundError as e:
        print(f"ERROR: Script not found. Make sure {e.filename} is in the same directory.")
    except Exception as e:
        print(f"An error occurred: {e}")