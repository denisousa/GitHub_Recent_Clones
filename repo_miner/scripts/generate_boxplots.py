import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def generate_boxplots():
    """
    Generates and saves boxplot charts for popularity metrics
    (stars, watchers, forks) from a consolidated data file.
    """
    print("🚀 Generating Boxplot charts for popularity distribution...")
    print("="*70)

    # --- SETTINGS ---
    # Consolidated input file
    input_file = os.path.join("results", "consolidated_master", "master_github_repos.json")
    
    # Output directory for the charts
    output_dir = "results"
    output_filename = os.path.join(output_dir, "popularity_distribution_boxplots.png")

    # --- 0. Loading and Validation ---
    if not os.path.exists(input_file):
        print(f"❌ Error: Input file not found at '{input_file}'")
        return

    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_json(input_file)
    print(f"✅ {len(df)} repositories loaded from '{input_file}'.")

    # --- 1. Chart Generation ---
    # Set the chart style
    sns.set_theme(style="whitegrid")

    # Create a figure with 3 subplots (1 row, 3 columns)
    fig, axes = plt.subplots(1, 3, figsize=(18, 8))
    fig.suptitle('Distribution of Repository Popularity Metrics', fontsize=16)

    metrics = ['stars', 'watchers', 'forks']
    titles = ['Stars', 'Watchers', 'Forks']

    for i, metric in enumerate(metrics):
        # Create the boxplot for the metric in the corresponding subplot
        sns.boxplot(ax=axes[i], y=df[metric], color='skyblue')
        axes[i].set_title(titles[i])
        axes[i].set_ylabel('Count')
        
        # IMPORTANT: Use a logarithmic scale for better visualization
        # The counts of stars/forks are very uneven (a few with millions, many with few).
        # The log scale makes the chart readable.
        axes[i].set_yscale('log')

    # Adjust the layout to prevent overlap
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # --- 2. Saving the Chart ---
    try:
        plt.savefig(output_filename)
        print(f"\n✅ Chart saved successfully to: '{output_filename}'")
    except Exception as e:
        print(f"\n❌ Error saving the chart: {e}")

    # Optional: show the chart on screen if running interactively
    # plt.show()


if __name__ == "__main__":
    generate_boxplots()