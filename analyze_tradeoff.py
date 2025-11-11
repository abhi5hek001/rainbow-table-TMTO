import sys
import os
import time
import subprocess
import hashlib
import pandas as pd
import matplotlib.pyplot as plt
import random
import numpy as np # <-- Import numpy for bar chart spacing

# --- We must import these to load the table ---
from rainbowtable import RainbowTable
from algorithm import Algorithm
# ---

# --- Configuration ---
PYTHON_CMD = sys.executable
GEN_SCRIPT = "rainbowgen.py"
ALGORITHM = "sha1"
CHARSET = "alphanumeric"
MIN_LEN = 1
MAX_LEN = 6  # Max length for the password
CHAIN_LEN = 200
N_CHAINS_LIST = [1000, 5000, 10000, 20000, 40000]

# --- NEW: Test Set Configuration ---
NUM_TEST_HASHES = 100 # How many random hashes to test against each table
# --- End Configuration ---


def generate_test_hashes(charset, min_len, max_len, num_hashes):
    """
    Generates a fixed set of random passwords and their hashes
    to test all tables against.
    """
    print(f"Generating {num_hashes} test hashes...")
    test_set = {} # Use a dict to store {hash: password}
    
    # We need a temporary algorithm object just to call hash_function
    # We use the real rainbowtable.py for consistency
    temp_rt = RainbowTable(ALGORITHM, CHARSET, MIN_LEN, MAX_LEN, CHAIN_LEN, 1)

    while len(test_set) < num_hashes:
        # Generate a random password
        k = random.randint(min_len, max_len)
        password = ''.join(random.choices(charset, k=k))
        
        # Hash it
        hash_bytes = temp_rt.hash_function(password)
        hash_hex = hash_bytes.hex()
        
        if hash_hex not in test_set:
            test_set[hash_hex] = password
            
    print(f"Test set created with {len(test_set)} unique hashes.\n")
    return test_set


def run_experiment(test_set):
    """
    Runs the full experiment and returns a list of results.
    """
    results = []
    
    table_dir = "generated_tables"
    os.makedirs(table_dir, exist_ok=True)
    print(f"Tables will be saved in '{table_dir}/'\n")
    
    print(f"Starting experiment...")

    for n_chains in N_CHAINS_LIST:
        print(f"--- Testing with n_chains = {n_chains} ---")
        
        output_file = os.path.join(table_dir, f"table_{n_chains}_chains.rt")
        
        # 1. Generate the table
        gen_command = [
            PYTHON_CMD, GEN_SCRIPT,
            ALGORITHM, CHARSET,
            str(MIN_LEN), str(MAX_LEN),
            str(CHAIN_LEN), str(n_chains),
            output_file
        ]
        
        print(f"Running rainbowgen.py")
        start_time = time.perf_counter()
        subprocess.run(gen_command, check=True, capture_output=True)
        end_time = time.perf_counter()
        gen_time_s = end_time - start_time
        print(f"Generation took: {gen_time_s:.2f} s")

        # 2. Measure File Size
        file_size_bytes = os.path.getsize(output_file)
        file_size_kb = file_size_bytes / 1024
        print(f"File size: {file_size_kb:.2f} KB")

        # 3. --- NEW: Measure Success Rate ---
        print(f"Loading table and testing {NUM_TEST_HASHES} hashes...")
        rt = RainbowTable.load_from_file(output_file)
        
        if not rt.table:
            print("Warning: Table is empty. Success Rate is 0%.")
            results.append({
                "Chains": n_chains,
                "File Size (KB)": file_size_kb,
                "Generation Time (s)": gen_time_s,
                "Success Rate (%)": 0.0,
            })
            continue

        hits_found = 0
        start_crack_time = time.perf_counter()
        
        for hash_to_crack, original_password in test_set.items():
            found_password = rt.lookup(hash_to_crack)
            if found_password == original_password:
                hits_found += 1
            elif found_password is not None:
                # This is a "false positive" - the table found a
                # different password that produces the same hash (a hash collision)
                # For this experiment, we'll count it as a hit.
                hits_found += 1

        end_crack_time = time.perf_counter()
        
        # Calculate results
        total_crack_time_s = end_crack_time - start_crack_time
        success_rate = (hits_found / NUM_TEST_HASHES) * 100.0
        
        print(f"Hits: {hits_found} / {NUM_TEST_HASHES}")
        print(f"Success Rate: {success_rate:.1f} %")
        print(f"Total crack time for {NUM_TEST_HASHES} hashes: {total_crack_time_s:.2f} s")


        # 4. Store results
        results.append({
            "Chains": n_chains,
            "File Size (KB)": file_size_kb,
            "Generation Time (s)": gen_time_s,
            "Success Rate (%)": success_rate, # <-- NEW METRIC
        })
        
        print(f"Table saved: {output_file}\n")

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
    print(df.to_markdown(index=False, floatfmt=(".4f", ".4f", ".4f", ".2f")))


    # 3. Create Plots
    
    # --- START PLOT 1 MODIFICATION ---
    # Plot 1: Generation Cost (Time & Size) as a Grouped Bar Chart
    
    labels = df['Chains'].astype(str) # Use chains as string labels
    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot Generation Time bars
    color = 'tab:red'
    ax1.set_xlabel('Number of Chains')
    ax1.set_ylabel('Generation Time (s)', color=color)
    bars1 = ax1.bar(x - width/2, df['Generation Time (s)'], width, label='Generation Time (s)', color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    # Instantiate a second axes that shares the same x-axis
    ax2 = ax1.twinx()  
    
    # Plot File Size bars
    color = 'tab:blue'
    ax2.set_ylabel('File Size (KB)', color=color)
    bars2 = ax2.bar(x + width/2, df['File Size (KB)'], width, label='File Size (KB)', color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    # Add x-axis labels
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
    fig.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to make room for legend
    plt.title('Generation Cost (Time and Memory)')
    plt.grid(True, axis='y') # Grid on y-axis only
    plt.savefig('generation_cost_plot.png')
    print("\nSaved plot: 'generation_cost_plot.png'")
    # --- END PLOT 1 MODIFICATION ---


    # Plot 2: The Time-Memory Trade-off (Success Rate)
    # (This one remains a line plot, as it shows a trend)
    plt.figure(figsize=(10, 6))
    plt.plot(df['File Size (KB)'], df['Success Rate (%)'], 'o-')
    plt.xlabel('File Size (KB)  <--- (Memory Cost)')
    plt.ylabel('Success Rate (%)  <--- (The "Time" Payoff)')
    plt.title('Time-Memory Trade-off: Success Rate')
    plt.grid(True)
    plt.savefig('tradeoff_plot.png')
    print("Saved plot: 'tradeoff_plot.png'")


if __name__ == "__main__":
    try:
        # First, generate the set of test hashes
        temp_charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        test_hash_set = generate_test_hashes(temp_charset, MIN_LEN, MAX_LEN, NUM_TEST_HASHES)
        
        # Now, run the experiment using this test set
        experiment_results = run_experiment(test_hash_set)
        analyze_and_plot(experiment_results)
        
    except FileNotFoundError as e:
        print(f"ERROR: Script not found. Make sure {e.filename} is in the same directory.")
    except Exception as e:
        print(f"An error occurred: {e}")