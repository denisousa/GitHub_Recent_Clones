import json
import csv
import glob
import os
from typing import List, Dict, Any

def consolidate_from_paths(source_paths: List[str]):
    """
    Consolidates the final results (JSON and CSV) from a specific list of
    run directories, removing any duplicates.

    :param source_paths: A list of paths to the directories containing
                         the results to be consolidated.
    """
    print("🚀 Starting consolidation from specific paths...")
    print("="*70)

    # --- Output Settings ---
    master_output_dir = os.path.join("results", "consolidated_master")
    master_json_file = os.path.join(master_output_dir, "master_github_repos.json")
    master_csv_file = os.path.join(master_output_dir, "master_github_repos.csv")
    
    # --- Consolidation Logic ---
    
    os.makedirs(master_output_dir, exist_ok=True)

    all_repos: Dict[str, Dict[str, Any]] = {}
    
    print("🔎 Processing the provided source directories...")
    
    # 1. Iterate over each provided path
    for path in source_paths:
        if not os.path.isdir(path):
            print(f"   ⚠️  Warning: The path '{path}' is not a valid directory. Skipping.")
            continue
            
        print(f"\n   -> Reading from: {path}")
        
        # Find the JSON file within the specified directory
        json_files_in_path = glob.glob(os.path.join(path, '*.json'))
        
        if not json_files_in_path:
            print(f"      - No JSON file found in '{path}'.")
            continue
            
        # Process the first JSON file found in the directory
        file_path = json_files_in_path[0]
        print(f"      - Processing file: {os.path.basename(file_path)}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                repos_from_file = json.load(f)
                for repo in repos_from_file:
                    if 'name' in repo:
                        # Use the repository name as the key to remove duplicates.
                        # If a repo is found in multiple paths, the one from the last path in the list will prevail.
                        all_repos[repo['name']] = repo
        except (json.JSONDecodeError, IOError) as e:
            print(f"      ❌ Error reading JSON file {file_path}: {e}")

    # Convert the dictionary back to a list
    final_unique_repos = list(all_repos.values())
    
    if not final_unique_repos:
        print("\n⚠️ No valid repositories were loaded. Aborting.")
        return
        
    print(f"\n✨ Total of {len(final_unique_repos)} unique repositories consolidated.")

    # 2. Save the master JSON file
    print(f"\n💾 Saving master JSON file to: {master_json_file}")
    try:
        with open(master_json_file, 'w', encoding='utf-8') as f:
            json.dump(final_unique_repos, f, ensure_ascii=False, indent=2)
        print("   ✅ Master JSON saved successfully.")
    except IOError as e:
        print(f"   ❌ Error saving master JSON file: {e}")

    # 3. Save the master CSV file
    print(f"\n💾 Saving master CSV file to: {master_csv_file}")
    try:
        headers = list(final_unique_repos[0].keys())
        
        with open(master_csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for repo in final_unique_repos:
                for key, value in repo.items():
                    if isinstance(value, (dict, list)):
                        repo[key] = json.dumps(value)
                writer.writerow(repo)
        print("   ✅ Master CSV saved successfully.")
    except (IOError, IndexError) as e:
        print(f"   ❌ Error saving master CSV file: {e}")
        
    print("\n🎉 Consolidation complete!")


if __name__ == "__main__":
    # --- ✅ CONFIGURE HERE ---
    # Add the paths to the results folders you want to consolidate.
    paths_to_consolidate = [
        "results_issue_close_3_days/final",
        "results_close_7_days_and_1000_stars/final",
        "results/final",
        # "results/final_another_config", # Example of how to add more
    ]
    
    consolidate_from_paths(paths_to_consolidate)
    