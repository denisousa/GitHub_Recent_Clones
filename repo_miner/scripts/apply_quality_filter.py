import pandas as pd
import json
import os

def get_project_category(row, quartiles):
    """
    Determines the quality category ('high', 'medium', 'lesser', or 'Excluded')
    for a single project based on its metrics compared to the calculated quartiles.
    """
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

def filter_and_categorize_dataset_fixed():
    """
    Main function to load, analyze, filter, and categorize the dataset,
    correctly handling data types to prevent JSON serialization errors.
    """
    # --- 1. Configuration ---
    input_file = 'results/consolidated_master/master_github_repos.json'
    output_dir = os.path.join("results", "final_categorized_dataset")
    output_file = os.path.join(output_dir, 'categorized_filtered_repos_final.json')

    if not os.path.exists(input_file):
        print(f"❌ Critical Error: Input file '{input_file}' not found.")
        return

    os.makedirs(output_dir, exist_ok=True)

    try:
        # --- 2. Load Data and Calculate Quartiles ---
        print("📄 Loading data for analysis using pandas...")
        df = pd.read_json(input_file)
        print(f"   Successfully loaded {len(df)} projects.")

        print("\n📊 Calculating quartiles (Q1 & Q3)...")
        quartiles = {
            'stars': (df['stars'].quantile(0.25), df['stars'].quantile(0.75)),
            'watchers': (df['watchers'].quantile(0.25), df['watchers'].quantile(0.75)),
            'forks': (df['forks'].quantile(0.25), df['forks'].quantile(0.75))
        }
        print("--- Quartile Calculation Results ---")
        print(f"   Stars    - Q1: {quartiles['stars'][0]}, Q3: {quartiles['stars'][1]}")
        print(f"   Watchers - Q1: {quartiles['watchers'][0]}, Q3: {quartiles['watchers'][1]}")
        print(f"   Forks    - Q1: {quartiles['forks'][0]}, Q3: {quartiles['forks'][1]}")
        print("------------------------------------")
        
        # --- 3. Classify Every Project ---
        print("\n🏷️  Assigning a quality category to every project...")
        df['quality_category'] = df.apply(lambda row: get_project_category(row, quartiles), axis=1)

        # --- 4. Identify Projects to Keep ---
        # Get the DataFrame containing only the projects we want to keep ('high', 'medium', 'lesser')
        filtered_df = df[df['quality_category'] != 'Excluded'].copy()
        print(f"\n🗑️  {len(df) - len(filtered_df)} projects will be removed ('Excluded').")
        print(f"   The final dataset will contain {len(filtered_df)} projects.")

        # --- 5. Build Final JSON from Original Data to Avoid Type Errors ---
        print(f"\n💾 Building final dataset and saving to '{output_file}'...")
        
        # Load the original raw file again to get pristine data types
        with open(input_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)

        final_data = []
        # Iterate through the indices of the *filtered* DataFrame
        for index in filtered_df.index:
            # Get the original project data using its index
            project_data = original_data[index]
            # Add the new category field
            project_data['quality_category'] = filtered_df.loc[index, 'quality_category']
            final_data.append(project_data)

        # --- 6. Save the Correctly Formatted Data ---
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)

        print("\n✅ Process complete! The new file has been saved successfully without data type errors.")

    except KeyError as e:
        print(f"\n❌ Key Error: A required column {e} was not found.")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

# --- Execute the main function ---
if __name__ == "__main__":
    filter_and_categorize_dataset_fixed()