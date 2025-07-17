import json
import csv
import glob
import os
import shutil
from typing import List, Dict, Any

def consolidate_with_organized_structure():
    """Consolidates all batches with an organized structure"""
    
    print("🔄 CONSOLIDATION WITH ORGANIZED STRUCTURE")
    print("="*60)
    
    # Settings
    OUTPUT_FILE = "github_repos_500.json"
    CSV_OUTPUT_FILE = "github_repos_500.csv"
    OUTPUT_ENCODING = "utf-8"
    
    # Create folder structure
    results_dir = "results"
    batches_dir = os.path.join(results_dir, "batches")
    final_dir = os.path.join(results_dir, "final")
    
    for directory in [results_dir, batches_dir, final_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Folder created: {directory}")
    
    # Move ALL batch files (JSON and CSV) to the new structure
    print(f"\n🔄 REORGANIZING BATCHES:")
    
    # Search for JSON and CSV in different locations
    search_patterns = [
        "batch_*_github_repos_500.json",           # Current folder - JSON
        "batch_*_github_repos_500.csv",            # Current folder - CSV
        os.path.join(results_dir, "batch_*_github_repos_500.json"),  # results/ - JSON
        os.path.join(results_dir, "batch_*_github_repos_500.csv"),   # results/ - CSV
    ]
    
    all_old_batches = []
    for pattern in search_patterns:
        found_files = glob.glob(pattern)
        all_old_batches.extend(found_files)
    
    # Remove duplicates while maintaining order
    seen = set()
    unique_old_batches = []
    for file in all_old_batches:
        if file not in seen:
            seen.add(file)
            unique_old_batches.append(file)
    
    moved_count = 0
    json_moved = 0
    csv_moved = 0
    
    for old_batch in unique_old_batches:
        try:
            filename = os.path.basename(old_batch)
            new_path = os.path.join(batches_dir, filename)
            
            # Check if it already exists in the destination folder
            if os.path.exists(new_path):
                print(f"   ⚠️ Already exists in batches/: {filename}")
                continue
            
            # Check if the file is not already in the batches folder
            if os.path.dirname(old_batch) == batches_dir:
                print(f"   ✅ Already in batches/: {filename}")
                continue
            
            # Move file
            shutil.move(old_batch, new_path)
            moved_count += 1
            
            if filename.endswith('.json'):
                json_moved += 1
                print(f"   ➡️ JSON moved: {filename}")
            elif filename.endswith('.csv'):
                csv_moved += 1
                print(f"   ➡️ CSV moved: {filename}")
            
        except Exception as e:
            print(f"   ❌ Error moving {old_batch}: {e}")
    
    if moved_count > 0:
        print(f"✅ {moved_count} files reorganized:")
        print(f"   📄 JSON: {json_moved}")
        print(f"   📊 CSV: {csv_moved}")
    else:
        print(f"✅ Files are already organized")
    
    # Search for all JSON batches in the new structure for consolidation
    batch_pattern = os.path.join(batches_dir, "batch_*_github_repos_500.json")
    batch_json_files = glob.glob(batch_pattern)
    
    # Search for all CSV batches for verification
    csv_pattern = os.path.join(batches_dir, "batch_*_github_repos_500.csv")
    batch_csv_files = glob.glob(csv_pattern)
    
    if not batch_json_files:
        print("❌ No JSON batch files found!")
        print(f"   📁 Searching in: {batch_pattern}")
        return False
    
    # Sort by batch number
    def extract_batch_number(filename):
        try:
            basename = os.path.basename(filename)
            parts = basename.split('_')
            return int(parts[1])
        except:
            return 0
    
    batch_json_files.sort(key=extract_batch_number)
    batch_csv_files.sort(key=extract_batch_number)
    
    print(f"\n📦 BATCHES FOLDER INVENTORY:")
    print(f"   📁 Batches folder: {batches_dir}")
    print(f"   📄 JSON found: {len(batch_json_files)}")
    print(f"   📊 CSV found: {len(batch_csv_files)}")
    
    # Check for corresponding JSON and CSV files
    json_numbers = [extract_batch_number(f) for f in batch_json_files]
    csv_numbers = [extract_batch_number(f) for f in batch_csv_files]
    
    missing_csv = [num for num in json_numbers if num not in csv_numbers]
    missing_json = [num for num in csv_numbers if num not in json_numbers]
    
    if missing_csv:
        print(f"   ⚠️ Batches without CSV: {missing_csv}")
    if missing_json:
        print(f"   ⚠️ Batches without JSON: {missing_json}")
    
    all_repos = []
    batch_stats = []
    total_repos = 0
    
    # Process each JSON batch
    for batch_file in batch_json_files:
        batch_num = extract_batch_number(batch_file)
        print(f"\n   📦 Processing batch_{batch_num:03d}...")
        
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
            
            repo_count = len(batch_data)
            
            # Check if a corresponding CSV exists
            corresponding_csv = os.path.join(batches_dir, f"batch_{batch_num:03d}_github_repos_500.csv")
            has_csv = os.path.exists(corresponding_csv)
            
            batch_stats.append({
                'batch': batch_num,
                'json_file': batch_file,
                'csv_file': corresponding_csv if has_csv else None,
                'repos': repo_count,
                'has_csv': has_csv
            })
            
            if repo_count > 0:
                all_repos.extend(batch_data)
                total_repos += repo_count
                status = "✅" if has_csv else "⚠️"
                print(f"      {status} +{repo_count} repositories {'(JSON+CSV)' if has_csv else '(JSON only)'}")
                
                # Show some names for verification
                if repo_count <= 3:
                    for repo in batch_data:
                        print(f"         • {repo.get('name', 'Name not found')}")
                else:
                    print(f"         • {batch_data[0].get('name', 'Name not found')}")
                    print(f"         • ... and {repo_count-1} more")
            else:
                status = "📝" if has_csv else "📝"
                print(f"      {status} Empty batch {'(JSON+CSV)' if has_csv else '(JSON only)'}")
                
        except Exception as e:
            print(f"      ❌ Error loading: {e}")
            batch_stats.append({
                'batch': batch_num,
                'json_file': batch_file,
                'csv_file': None,
                'repos': 0,
                'has_csv': False,
                'error': str(e)
            })
    
    # Sequence analysis
    batch_numbers = [stat['batch'] for stat in batch_stats if 'error' not in stat]
    if batch_numbers:
        min_batch = min(batch_numbers)
        max_batch = max(batch_numbers)
        expected_range = list(range(min_batch, max_batch + 1))
        missing_batches = [b for b in expected_range if b not in batch_numbers]
        
        print(f"\n🔍 SEQUENCE ANALYSIS:")
        print(f"   📊 Range: batch_{min_batch:03d} to batch_{max_batch:03d}")
        print(f"   ✅ Batches found: {len(batch_numbers)}")
        
        if missing_batches:
            print(f"   ⚠️ Missing batches: {missing_batches}")
            print(f"      💡 This is normal if these batches were empty")
        else:
            print(f"   🎉 Complete sequence!")
    
    print(f"\n📊 CONSOLIDATION SUMMARY:")
    print(f"   🔢 JSON files processed: {len(batch_json_files)}")
    print(f"   📊 CSV files available: {len(batch_csv_files)}")
    print(f"   ✅ Total repositories: {total_repos}")
    
    if total_repos == 0:
        print("⚠️ No repositories found to consolidate!")
        return False
    
    # Remove duplicates
    unique_repos = []
    seen_names = set()
    duplicates = 0
    
    for repo in all_repos:
        repo_name = repo.get('name', '')
        if repo_name and repo_name not in seen_names:
            unique_repos.append(repo)
            seen_names.add(repo_name)
        elif repo_name:
            duplicates += 1
            print(f"   🧹 Duplicate removed: {repo_name}")
    
    final_count = len(unique_repos)
    
    if duplicates > 0:
        print(f"   🧹 Duplicates removed: {duplicates}")
    
    print(f"   🎯 Unique repositories: {final_count}")
    
    # Save final files to the final/ folder
    print(f"\n💾 SAVING FINAL FILES:")
    print(f"   📁 Final results folder: {final_dir}")
    
    final_json_path = os.path.join(final_dir, OUTPUT_FILE)
    final_csv_path = os.path.join(final_dir, CSV_OUTPUT_FILE)
    
    try:
        print(f"   📄 Saving JSON: {final_json_path}")
        with open(final_json_path, 'w', encoding=OUTPUT_ENCODING) as f:
            json.dump(unique_repos, f, ensure_ascii=False, indent=2)
        print(f"   ✅ JSON saved: {final_json_path} ({final_count} repositories)")
    except Exception as e:
        print(f"   ❌ Error saving JSON: {e}")
        return False
    
    try:
        print(f"   📊 Saving CSV: {final_csv_path}")
        
        if unique_repos:
            fieldnames = list(unique_repos[0].keys())
            
            with open(final_csv_path, 'w', newline='', encoding=OUTPUT_ENCODING) as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(unique_repos)
            
            print(f"   ✅ CSV saved: {final_csv_path} ({final_count} repositories)")
        else:
            print(f"   ⚠️ No repositories to save to CSV")
            
    except Exception as e:
        print(f"   ❌ Error saving CSV: {e}")
        return False
    
    # Detailed final report
    print(f"\n📋 FINAL ORGANIZED STRUCTURE:")
    print(f"   📁 {results_dir}/")
    print(f"   ├── 📁 batches/          ({len(batch_json_files)} JSON + {len(batch_csv_files)} CSV)")
    
    # Show some file examples
    sample_batches = batch_json_files[:3]
    for batch_file in sample_batches:
        batch_num = extract_batch_number(batch_file)
        json_name = f"batch_{batch_num:03d}_github_repos_500.json"
        csv_name = f"batch_{batch_num:03d}_github_repos_500.csv"
        csv_exists = os.path.exists(os.path.join(batches_dir, csv_name))
        
        print(f"   │   ├── 📄 {json_name}")
        if csv_exists:
            print(f"   │   ├── 📊 {csv_name}")
    
    if len(batch_json_files) > 3:
        print(f"   │   └── ... and more files")
    
    print(f"   └── 📁 final/            (2 files)")
    print(f"       ├── 📄 {OUTPUT_FILE}")
    print(f"       └── 📊 {CSV_OUTPUT_FILE}")
    
    print(f"\n🎉 CONSOLIDATION COMPLETED SUCCESSFULLY!")
    print(f"   🎯 Total consolidated: {final_count} unique repositories")
    print(f"   📁 Results in: {final_dir}")
    print(f"   📦 Batches organized in: {batches_dir}")
    
    return True

if __name__ == "__main__":
    consolidate_with_organized_structure()