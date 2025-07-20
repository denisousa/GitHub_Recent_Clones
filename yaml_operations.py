import os
import yaml
import pandas as pd

def extract_blocks_to_csv(yaml_path: str, csv_output_path: str, filename_add_new: str):
    with open(yaml_path, "r", encoding="utf-8") as f:
        simian_data = yaml.safe_load(f.read().split('---')[-1])

    blocks_data = []
    sets = simian_data.get("simian", {}).get("checks", [])[0].get("sets", [])

    for item in sets:
        if isinstance(item, dict) and "blocks" in item:
            fingerprint = item.get("fingerprint", "")
            for block in item["blocks"]:
                source_file = block.get("sourceFile", "")
                if "blocks_added" in source_file:

                    for b in item["blocks"]:
                        blocks_data.append({
                            "fingerprint": fingerprint,
                            "sourceFile": b.get("sourceFile").split('GitHub_Recent_Clones')[-1],
                            "startLineNumber": b.get("startLineNumber"),
                            "endLineNumber": b.get("endLineNumber"),
                            "NEWsourceFile": filename_add_new
                        })
                break

    new_df = pd.DataFrame(blocks_data)

    if os.path.exists(csv_output_path):
        try:
            existing_df = pd.read_csv(csv_output_path)
        except pd.errors.EmptyDataError:
            print('Error!')
            existing_df = pd.DataFrame()  # treat as empty
    else:
        existing_df = pd.DataFrame()

    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df.drop_duplicates(
        subset=["fingerprint", "sourceFile", "startLineNumber", "endLineNumber"],
        inplace=True
    )

    combined_df.to_csv(csv_output_path, index=False)
    print(f"CSV generated at: {csv_output_path}")
    return csv_output_path
