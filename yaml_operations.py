import os
import yaml
import pandas as pd

def check_added_clones(blocks_list):
    qtd_diffs = len([block for block in blocks_list if f"blocks_added" in block.get("sourceFile", "")]) 
    qtd_existing = len([block for block in blocks_list if f"blocks_added" not in block.get("sourceFile", "")]) 

    more_than_one_diff = qtd_diffs > 1 
    more_than_one_existing = qtd_existing > 1
    exists_between = qtd_diffs >= 1 and qtd_existing >= 1
    
    if exists_between and more_than_one_diff and more_than_one_existing:
        return {
            'scenario': 'Increased the number of clones with multiple clones.',
            'severity': 5,
            'effect': 'Increase clones',
            'new clones': 'Multiple'
        }
    
    if exists_between and more_than_one_existing:
        return {
            'scenario': 'Increased the number of clones with one clone.',
            'severity': 3,
            'effect': 'Increase clones',
            'new clones': 'One'
        }

    if exists_between and more_than_one_diff:
        return {
            'scenario': 'Created multiple clones between new code with one existing code.',
            'severity': 4,
            'effect': 'Creation clones',
            'new clones': 'Multiple'
        }
    
    if exists_between:
        return {
            'scenario': 'Created one clone between existing code and new code.',
            'severity': 1,
            'effect': 'Creation clones',
            'new clones': 'One'
        }
    
    if more_than_one_diff:
        return {
            'scenario': 'Created multiple clones only between the new code.',
            'severity': 2,
            'effect': 'Creation clones',
            'new clones': 'Multiple'
        }

    if more_than_one_existing:
        return {
            'scenario': 'No action on clones.',
            'severity': 0,
            'effect': 'Nothing',
            'new clones': 'Nothing'
        }

def check_removed_clones(blocks_list):
    qtd_diffs = len([block for block in blocks_list if f"blocks_removed" in block.get("sourceFile", "")]) 
    qtd_existing = len([block for block in blocks_list if f"blocks_removed" not in block.get("sourceFile", "")]) 

    more_than_one_diff = qtd_diffs > 1 
    more_than_one_existing = qtd_existing > 1
    exists_between = qtd_diffs >= 1 and qtd_existing >= 1
    
    if exists_between and more_than_one_diff and more_than_one_existing:
        return {
            'scenario': 'Removed multiple clones between new and existing code.',
            'correctness': 5,
            'effect': 'Remove clones',
            'new clones': 'Multiple'
        }

    if exists_between and more_than_one_existing:
        return {
            'scenario': 'Removed one clone between new and existing code.',
            'correctness': 3,
            'effect': 'Remove clones',
            'new clones': 'One'
        }

    if exists_between and more_than_one_diff:
        return {
            'scenario': 'Strange case: removed multiple clones from new code only.',
            'correctness': 4,
            'effect': 'Remove clones',
            'new clones': 'Multiple'
        }

    if exists_between:
        return {
            'scenario': 'Removed one clone (complete removal).',
            'correctness': 1,
            'effect': 'Complete Removal',
            'new clones': 'One'
        }

    if more_than_one_diff:
        return {
            'scenario': 'Strange case: removed multiple clones from new code only.',
            'correctness': 2,
            'effect': 'Remove clones',
            'new clones': 'Multiple'
        }

    if more_than_one_existing:
        return {
            'scenario': 'No action on clones.',
            'correctness': 0,
            'effect': 'Nothing',
            'new clones': 'Nothing'
        }


def get_category(blocks, type_operation):
    if 'added' == type_operation:
        return check_added_clones(blocks)
    else:
        return  check_removed_clones(blocks)


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
                    "yaml_path": yaml_path,
                }
                # Adiciona todos os campos de info_df
                block_info.update(info_df)
                block_info.update(category)
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
    # combined_df.drop_duplicates(
    #     subset=["fingerprint", "sourceFile", "startLineNumber", "endLineNumber"],
    #     inplace=True
    # )

    combined_df.to_csv(csv_output_path, index=False)
    print(f"CSV atualizado em: {csv_output_path}")
    return csv_output_path