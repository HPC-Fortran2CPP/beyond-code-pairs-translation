import json

def reduce_dataset(input_file, output_file, max_entries=100):
    """
    Read a large JSON dataset and create a smaller file with only the first N entries.
    
    Args:
        input_file: Path to the original JSON file
        output_file: Path to save the reduced JSON file
        max_entries: Number of entries to keep (default: 100)
    """
    # Read the original file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Keep only the first max_entries
    reduced_data = data[:max_entries]
    
    # Write to new file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(reduced_data, f, indent=4, ensure_ascii=False)
    
    print(f"Original entries: {len(data)}")
    print(f"Reduced entries: {len(reduced_data)}")
    print(f"Saved to: {output_file}")

# Usage
if __name__ == "__main__":
    reduce_dataset('f2c_dialogue_test.jsonl', 'f2c_dialogue_test.json', max_entries=100)