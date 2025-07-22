import os
import yaml
import pandas as pd

def check_cb(blocks_list, type_operation):
    if len([block for block in blocks_list if f"blocks_{type_operation}" in block.get("sourceFile", "")]) > 1:
        return True
    return False

def check_oc(blocks_list, type_operation):
    if len([block for block in blocks_list if f"blocks_{type_operation}" not in block.get("sourceFile", "")]) > 1:
        return True
    return False

def check_cboc(blocks_list, type_operation):
    len_bb = len([block for block in blocks_list if f"blocks_{type_operation}" in block.get("sourceFile", "")]) >= 1
    len_bo = len([block for block in blocks_list if f"blocks_{type_operation}" not in block.get("sourceFile", "")]) >= 1
    
    if len_bb and len_bo:
        return True
    return False

def get_category(blocks, type_operation):
    category = []
    validy_cb = check_cb(blocks, type_operation)
    validy_oc = check_oc(blocks, type_operation)
    validy_cboc = check_cboc(blocks, type_operation)

    if validy_cb:
        category.append('C.B')

    if validy_oc:
        category.append('O.C')

    if validy_cboc:
        category.append('C.B.O.C')
    
    return category

def extract_blocks_to_csv(yaml_path: str, info_df: dict, type_operation):
    with open(yaml_path, "r", encoding="utf-8") as f:
        simian_data = yaml.safe_load(f.read().split('---')[-1])

    blocks_data = []
    sets = simian_data.get("simian", {}).get("checks", [])[0].get("sets", [])

    for item in sets:
        if isinstance(item, dict) and "blocks" in item:
            fingerprint = item.get("fingerprint", "")
            
            category = get_category(item["blocks"], type_operation)
            for i, block in enumerate(item["blocks"]):
                block_info = {
                    "fingerprint": fingerprint,
                    "sourceFile": block.get("sourceFile").split('GitHub_Recent_Clones')[-1],
                    "startLineNumber": block.get("startLineNumber"),
                    "endLineNumber": block.get("endLineNumber"),
                    "category": category,
                    "yaml_path": yaml_path,
                }
                # Adiciona todos os campos de info_df
                block_info.update(info_df)
                blocks_data.append(block_info)


    new_df = pd.DataFrame(blocks_data)

    csv_output_path = f"{type_operation}_result.csv"
    if os.path.exists(csv_output_path):
        try:
            existing_df = pd.read_csv(csv_output_path)
        except pd.errors.EmptyDataError:
            print('Error! CSV vazio.')
            existing_df = pd.DataFrame()  # trata como vazio
    else:
        existing_df = pd.DataFrame()

    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df.drop_duplicates(
        subset=["fingerprint", "sourceFile", "startLineNumber", "endLineNumber"],
        inplace=True
    )

    combined_df.to_csv(csv_output_path, index=False)
    print(f"CSV atualizado em: {csv_output_path}")
    return csv_output_path