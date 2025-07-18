import json
import csv
import glob
import os
import shutil
import pandas as pd
from typing import List, Dict, Any

class DataProcessor:
    """
    A class to consolidate, filter, and categorize GitHub repository data.
    """
    def __init__(self, base_filename: str):
        """
        Initializes the processor with filenames and directory settings.

        Args:
            base_filename (str): The base name for batch and output files (e.g., 'github_repos_500').
        """
        self.base_filename = base_filename
        
        # Output filenames
        self.output_json_file = f"{self.base_filename}.json"
        self.output_csv_file = f"{self.base_filename}.csv"
        self.final_categorized_file = f"github_pr_repos_dataset.json"

        # Directory structure
        self.results_dir = "results"
        self.batches_dir = os.path.join(self.results_dir, "batches")
        self.final_dir = os.path.join(self.results_dir, "final")

        # Full paths to final files
        self.final_json_path = os.path.join(self.final_dir, self.output_json_file)
        self.final_csv_path = os.path.join(self.final_dir, self.output_csv_file)
        self.final_categorized_path = os.path.join(self.final_dir, self.final_categorized_file)

    def _extract_batch_number(self, filename: str) -> int:
        """Extracts the batch number from the filename."""
        try:
            basename = os.path.basename(filename)
            return int(basename.split('_')[1])
        except (IndexError, ValueError):
            return 0

    def _get_project_category(self, row: pd.Series, quartiles: Dict[str, tuple]) -> str:
        """Determines the quality category of a project based on quartiles."""
        q1_stars, q3_stars = quartiles['stars']
        q1_watchers, q3_watchers = quartiles['watchers']
        q1_forks, q3_forks = quartiles['forks']

        stars, watchers, forks = row['stars'], row['watchers'], row['forks']

        if (stars >= q3_stars) and (watchers >= q3_watchers) and (forks >= q3_forks):
            return 'high'
        if (stars <= q1_stars) and (watchers <= q1_watchers) and (forks <= q1_forks):
            return 'lesser'
        if (q1_stars < stars <= q3_stars) and \
           (q1_watchers < watchers <= q3_watchers) and \
           (q1_forks < forks <= q3_forks):
            return 'medium'
        
        return 'Excluded'

    def _consolidate_batches(self) -> str or None: # type: ignore
        """Consolidates all partial batches into single JSON and CSV files."""
        print("\n🔄 STARTING DATA CONSOLIDATION")
        print("="*60)
        
        # Create the folder structure
        for directory in [self.results_dir, self.batches_dir, self.final_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Reorganize batch files
        print("🔄 REORGANIZING BATCHES:")
        search_patterns = [
            f"batch_*_{self.base_filename}.json",
            f"batch_*_{self.base_filename}.csv",
            os.path.join(self.results_dir, f"batch_*_{self.base_filename}.json"),
            os.path.join(self.results_dir, f"batch_*_{self.base_filename}.csv"),
        ]
        all_old_batches = [file for pattern in search_patterns for file in glob.glob(pattern)]
        unique_old_batches = sorted(list(set(all_old_batches)))
        
        moved_count = 0
        for old_batch in unique_old_batches:
            if os.path.dirname(old_batch) != self.batches_dir:
                shutil.move(old_batch, self.batches_dir)
                moved_count += 1
        
        if moved_count > 0:
            print(f"✅ {moved_count} files reorganized to '{self.batches_dir}'")
        else:
            print("✅ Files are already organized.")

        # Consolidation
        batch_pattern = os.path.join(self.batches_dir, f"batch_*_{self.base_filename}.json")
        batch_json_files = sorted(glob.glob(batch_pattern), key=self._extract_batch_number)

        if not batch_json_files:
            print(f"❌ No JSON batch files found in: {batch_pattern}")
            return None

        all_repos = []
        for batch_file in batch_json_files:
            with open(batch_file, 'r', encoding='utf-8') as f:
                all_repos.extend(json.load(f))

        # Remove duplicates
        unique_repos, seen_names, duplicates = [], set(), 0
        for repo in all_repos:
            if (repo_name := repo.get('name')) and repo_name not in seen_names:
                unique_repos.append(repo)
                seen_names.add(repo_name)
            else:
                duplicates += 1
        
        if duplicates > 0:
            print(f"🧹 {duplicates} duplicates removed.")
        
        print(f"🎯 Total unique repositories: {len(unique_repos)}")
        
        # Save final files
        print(f"💾 Saving final files to: {self.final_dir}")
        with open(self.final_json_path, 'w', encoding='utf-8') as f:
            json.dump(unique_repos, f, ensure_ascii=False, indent=2)
        print(f"   📄 JSON saved: {self.final_json_path}")
        
        if unique_repos:
            with open(self.final_csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=unique_repos[0].keys())
                writer.writeheader()
                writer.writerows(unique_repos)
            print(f"   📊 CSV saved: {self.final_csv_path}")

        print("🎉 CONSOLIDATION COMPLETED SUCCESSFULLY!")
        return self.final_json_path

    def _filter_and_categorize(self, input_json_path: str) -> str or None: # type: ignore
        """Filters and categorizes the consolidated dataset."""
        print("\n🔄 STARTING FILTERING AND CATEGORIZATION")
        print("="*60)

        if not os.path.exists(input_json_path):
            print(f"❌ Critical Error: Input file '{input_json_path}' not found.")
            return None

        try:
            print("📄 Loading data for analysis with pandas...")
            df = pd.read_json(input_json_path)
            print(f"   Successfully loaded {len(df)} projects.")

            print("\n📊 Calculating quartiles (Q1 & Q3)...")
            quartiles = {
                'stars': (df['stars'].quantile(0.25), df['stars'].quantile(0.75)),
                'watchers': (df['watchers'].quantile(0.25), df['watchers'].quantile(0.75)),
                'forks': (df['forks'].quantile(0.25), df['forks'].quantile(0.75))
            }

            # --- Quartile Calculation Results ---
            print("--- Quartile Calculation Results ---")
            print(f"   Stars    - Q1: {quartiles['stars'][0]:.0f}, Q3: {quartiles['stars'][1]:.0f}")
            print(f"   Watchers - Q1: {quartiles['watchers'][0]:.0f}, Q3: {quartiles['watchers'][1]:.0f}")
            print(f"   Forks    - Q1: {quartiles['forks'][0]:.0f}, Q3: {quartiles['forks'][1]:.0f}")
            print("--------------------------------------")
            
            print("\n🏷️  Assigning quality categories...")
            df['quality_category'] = df.apply(lambda row: self._get_project_category(row, quartiles), axis=1)

            filtered_df = df[df['quality_category'] != 'Excluded'].copy()
            print(f"🗑️  {len(df) - len(filtered_df)} projects removed ('Excluded').")
            print(f"   The final dataset will contain {len(filtered_df)} projects.")

            print(f"💾 Building final dataset and saving to '{self.final_categorized_path}'...")
            with open(input_json_path, 'r', encoding='utf-8') as f:
                original_data = json.load(f)

            final_data = []
            for index in filtered_df.index:
                project_data = original_data[index]
                project_data['quality_category'] = filtered_df.loc[index, 'quality_category']
                final_data.append(project_data)

            with open(self.final_categorized_path, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=4)
            
            print("🎉 FILTERING AND CATEGORIZATION COMPLETED SUCCESSFULLY!")
            return self.final_categorized_path

        except Exception as e:
            print(f"\n❌ An unexpected error occurred during filtering: {e}")
            return None

    def process(self):
        """
        Executes the complete post-processing workflow: consolidation and then filtering.
        """
        consolidated_file = self._consolidate_batches()
        if consolidated_file:
            self._filter_and_categorize(consolidated_file)