import sys
import os

# We need to import the class so pickle knows how to "unpickle" the object
from rainbowtable import RainbowTable
from algorithm import Algorithm


if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} <table_file.rt>")
    sys.exit(1)

file_path = sys.argv[1]

if not os.path.exists(file_path):
    print(f"ERROR: File not found: {file_path}")
    sys.exit(1)

print(f"--- Loading table: {file_path} ---")

try:
    # load_from_file handles the unpickling
    rt = RainbowTable.load_from_file(file_path)

    print("\n=== Table Parameters ===")
    print(f"  Algorithm: {rt.algorithm.name}")
    print(f"  Charset: {rt.charset}")
    print(f"  Min Length: {rt.min_length}")
    print(f"  Max Length: {rt.max_length}")
    print(f"  Chain Length: {rt.chain_length}")
    print(f"  Number of Chains: {rt.number_of_chains}")

    print("\n=== Table Data (Sample) ===")
    # The 'table' attribute is a dictionary
    print(f"  Total chains stored: {len(rt.table)}")

    # Get first 10 items as a sample to avoid flooding the console
    print("  Showing first 10 chains (Tail-Hash : Head-Password):")
    count = 0
    for tail_hash_bytes, head_password in rt.table.items():
        if count >= 10:
            print("  ... (and more)")
            break
        # tail_hash is binary, so print its hex representation
        print(f"    {tail_hash_bytes.hex()} : {head_password}")
        count += 1

except Exception as e:
    print(f"\nERROR: Could not load or read the table file.")
    print(f"Details: {e}")
    print("Make sure this is a valid .rt file and you are in your correct (crypto) environment.")