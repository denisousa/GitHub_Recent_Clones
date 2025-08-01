import pandas as pd

def analyze_removed_result(csv_path):
    # Load the CSV file
    df = pd.read_csv(csv_path)

    # Count unique fingerprints
    unique_fingerprints = df['fingerprint'].nunique()

    # Count unique PR numbers
    unique_pr_numbers = df['pr_number'].nunique()

    # Convert 'category' column to string (in case it's a list-like object)
    df['category_str'] = df['category'].astype(str)

    # Count unique categories
    unique_categories = df['category_str'].nunique()

    # Count occurrences of each category
    category_counts = df['category_str'].value_counts()

    # Display results
    print(f"\nAnalysis for: {csv_path}")
    print(f"Number of unique fingerprints: {unique_fingerprints}")
    print(f"Number of unique PR numbers: {unique_pr_numbers}")
    print(f"Number of unique categories: {unique_categories}")
    print("\nCategory frequency:")
    for category, count in category_counts.items():
        print(f"  {category}: {count} occurrence(s)")

# Run the function on both files
analyze_removed_result("added_result.csv")
analyze_removed_result("removed_result.csv")
