import json
import csv
import glob
import os
import shutil
import pandas as pd
from typing import Dict

class PostProcessor:
    """
    Handles post-mining tasks: consolidating batches and applying quality filters.
    """

    def __init__(self, results_dir="results"):
        """Initializes the post-processor with default paths."""
        self.results_dir = results_dir
        self.batches_dir = os.path.join(self.results_dir, "batches")
        self.partial_results_dir = os.path.join(self.results_dir, "partial")
        self.final_dir = os.path.join(self.results_dir, "final")
        
        # Configuration for filenames
        self.consolidated_json_file = os.path.join(self.partial_results_dir, "consolidated_repos.json")
        self.consolidated_csv_file = os.path.join(self.partial_results_dir, "consolidated_repos.csv")
        self.categorized_output_file = os.path.join(self.final_dir, 'github_pr_repos_dataset.json')

    def consolidate_batches(self, batch_file_pattern: str = "batch_*.json") -> bool:
        """Consolidates all batch files into a single JSON and CSV."""
        print("\n" + "="*60)
        print("🔄 Starting batch consolidation...")
        
        os.makedirs(self.final_dir, exist_ok=True)
        
        search_pattern = os.path.join(self.batches_dir, batch_file_pattern)
        batch_files = sorted(glob.glob(search_pattern))

        if not batch_files:
            print(f"⚠️ No batch files found with pattern '{search_pattern}'. Nothing to consolidate.")
            return False

        all_repos_map: Dict[str, Dict] = {}
        for batch_file in batch_files:
            try:
                with open(batch_file, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)
                    for repo in batch_data:
                        # Use repo name as key to auto-handle duplicates across batches
                        if 'name' in repo:
                            all_repos_map[repo['name']] = repo
            except Exception as e:
                print(f"   ❌ Error reading batch file {os.path.basename(batch_file)}: {e}")

        if not all_repos_map:
            print("⚠️ No repositories were loaded from batch files.")
            return False
            
        unique_repos = list(all_repos_map.values())
        print(f"   ✅ Found {len(batch_files)} batches, consolidated into {len(unique_repos)} unique repositories.")

        # Save consolidated JSON
        try:
            with open(self.consolidated_json_file, 'w', encoding='utf-8') as f:
                json.dump(unique_repos, f, ensure_ascii=False, indent=2)
            print(f"   💾 Consolidated JSON saved to: {self.consolidated_json_file}")
        except Exception as e:
            print(f"   ❌ Error saving consolidated JSON: {e}")
            return False

        # Save consolidated CSV
        try:
            if unique_repos:
                fieldnames = list(unique_repos[0].keys())
                with open(self.consolidated_csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(unique_repos)
                print(f"   💾 Consolidated CSV saved to: {self.consolidated_csv_file}")
        except Exception as e:
            print(f"   ❌ Error saving consolidated CSV: {e}")

        print("🎉 Consolidation completed successfully!")
        return True

    def _get_project_category(self, row: pd.Series, quartiles: Dict) -> str:
        """Determines the quality category for a project based on quartiles."""
        q1_stars, q3_stars = quartiles['stars']
        q1_watchers, q3_watchers = quartiles['watchers']
        q1_forks, q3_forks = quartiles['forks']
        stars, watchers, forks = row['stars'], row['watchers'], row['forks']

        if (stars >= q3_stars) and (watchers >= q3_watchers) and (forks >= q3_forks):
            return 'high'
        if (stars <= q1_stars) and (watchers <= q1_watchers) and (forks <= q1_forks):
            return 'lesser'
        if (q1_stars < stars < q3_stars) and (q1_watchers < watchers < q3_watchers) and (q1_forks < forks < q3_forks):
            return 'medium'
        return 'Excluded'

    def apply_quality_filter(self) -> bool:
        """Filters and categorizes the consolidated dataset based on popularity metrics."""
        print("\n" + "="*60)
        print("🏷️  Applying quality filter and categorizing dataset...")

        if not os.path.exists(self.consolidated_json_file):
            print(f"❌ Error: Consolidated file not found at '{self.consolidated_json_file}'. Run consolidation first.")
            return False

        os.makedirs(self.final_categorized_dir, exist_ok=True)
        
        try:
            df = pd.read_json(self.consolidated_json_file)
            print(f"   📄 Loaded {len(df)} projects for analysis.")

            quartiles = {
                'stars': (df['stars'].quantile(0.25), df['stars'].quantile(0.75)),
                'watchers': (df['watchers'].quantile(0.25), df['watchers'].quantile(0.75)),
                'forks': (df['forks'].quantile(0.25), df['forks'].quantile(0.75))
            }
            print("   📊 Calculated quartiles (Q1 & Q3) for popularity metrics.")

            df['quality_category'] = df.apply(lambda row: self._get_project_category(row, quartiles), axis=1)
            
            filtered_df = df[df['quality_category'] != 'Excluded'].copy()
            print(f"   🗑️  {len(df) - len(filtered_df)} projects excluded. {len(filtered_df)} projects remain.")

            # Convert dataframe to dict for JSON serialization
            final_data = filtered_df.to_dict(orient='records')

            with open(self.categorized_output_file, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=4)
            print(f"   💾 Categorized and filtered dataset saved to: {self.categorized_output_file}")
            
            print("🎉 Quality filtering completed successfully!")
            return True
        except Exception as e:
            print(f"   ❌ An unexpected error occurred during filtering: {e}")
            return False