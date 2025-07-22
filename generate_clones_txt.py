import pandas as pd
import os

def generate_code_report_from_csv(csv_path: str, output_txt: str = "code_report.txt"):
    df = pd.read_csv(csv_path)

    with open(output_txt, "w", encoding="utf-8") as out_file:
        for _, row in df.iterrows():
            fingerprint = row["fingerprint"]
            source_file = row["sourceFile"].lstrip("/")  # remove leading slash if present
            start = int(row["startLineNumber"])
            end = int(row["endLineNumber"])

            # Skip if the file doesn't exist
            if not os.path.exists(source_file):
                out_file.write(f"---\nFINGERPRINT: {fingerprint}\nFILE: {source_file} (NOT FOUND)\n\n")
                continue

            # Read specified lines from the file
            with open(source_file, "r", encoding="utf-8") as src:
                lines = src.readlines()
                snippet = lines[start - 1:end]  # lines are 1-indexed in the CSV

            # Write to the output file
            out_file.write(f"---\nFINGERPRINT: {fingerprint}\nFILE: {source_file}\nLINES: {start}-{end}\n")
            out_file.write("CODE:\n")
            out_file.writelines(snippet)
            out_file.write("\n")

    print(f"Code report generated: {output_txt}")
    return output_txt

generate_code_report_from_csv("added_result.csv", "code_report_added.txt")
generate_code_report_from_csv("removed_result.csv", "code_report_removed.txt")
