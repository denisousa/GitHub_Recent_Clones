from dotenv import load_dotenv
from lsh_operation import filter_unique_code_blocks
from github_operations import fetch_recent_merged_prs, extract_java_diffs_from_pr, clone_and_checkout_pr_base_commit
from simian_operations import execute_simian
from yaml_operations import extract_blocks_to_csv
from datetime import datetime
import random
import string
import os
import re

load_dotenv()
token = os.getenv("GH_TOKEN")

def save_code_blocks(type_folder, blocks: dict, base_dir: str = "."):
    block_list = blocks.get(type_folder, [])
    os.makedirs('blocks', exist_ok=True)

    hash_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    folder_name = f"blocks/blocks_{type_folder}_{hash_suffix}"
    folder_path = os.path.join(base_dir, folder_name)

    os.system(f'rm -rf "{folder_path}"')
    os.makedirs(folder_path)

    for i, code in enumerate(block_list, start=1):
        file_path = os.path.join(folder_path, f"block_{i}.java")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

    print(f"Saved {len(block_list)} blocks to '{folder_name}'")

    return folder_path

def remove_prints_comments_and_blank_lines(java_code: str) -> str:
    java_code = re.sub(r'/\*[\s\S]*?\*/', '', java_code)
    java_code = re.sub(r'//.*', '', java_code)
    java_code = re.sub(
        r'\bSystem\.out\.print(?:ln)?\s*\((?:[^()"]+|"(?:\\.|[^"\\])*")*\)\s*;',
        '', java_code
    )
    java_code = "\n".join(line for line in java_code.splitlines() if line.strip())
    return java_code

def clean_java_code(java_code):
    # TODO: Put Formatter Java Code
    cleaned_code = remove_prints_comments_and_blank_lines(java_code)
    return cleaned_code

def extract_valid_blocks(diff_file_path, min_block_size):
    with open(diff_file_path, encoding='utf-8') as file:
        lines = file.readlines()

    code_block = {'added': [], 'removed': []}
    current_block = []  # Store current block lines without '+' or '-'
    current_type = None  # '+' or '-'

    for line in lines[3:]:  # Skip first 3 diff lines
        if line.startswith('+') or line.startswith('-'):
            content = line[1:]  # Remove '+' or '-'

            if current_type is None:
                current_type = line[0]
                current_block = [content]
            elif current_type == line[0]:
                current_block.append(content)
            else:
                # Store previous block if large enough
                if len(current_block) >= min_block_size:
                    if current_type == '-':
                        code_block['removed'].append(''.join(current_block))
                    elif current_type == '+':
                        code_block['added'].append(''.join(current_block))

                # Start new block
                current_type = line[0]
                current_block = [content]
        else:
            # Non-modified line → finalize current block if needed
            if len(current_block) >= min_block_size:
                if current_type == '-':
                    code_block['removed'].append(''.join(current_block))
                elif current_type == '+':
                    code_block['added'].append(''.join(current_block))

            current_type = None
            current_block = []

    # Final check for last block
    if len(current_block) >= min_block_size:
        if current_type == '-':
            code_block['removed'].append(''.join(current_block))
        elif current_type == '+':
            code_block['added'].append(''.join(current_block))

    return code_block

def generate_diff_file(file, filename: str) -> None:
    diff_text = ''
    new_filename =  filename.split('/')[-1].replace('.java','')
    new_filename = filename.split('/')[-2] + '@' + new_filename
    if file.patch:  # Alguns arquivos podem não ter patch, como arquivos binários
        diff_text += f"diff --git a/{file.filename} b/{file.filename}\n"
        diff_text += f"--- a/{file.filename}\n"
        diff_text += f"+++ b/{file.filename}\n"
        diff_text += file.patch + "\n"

    complete_path_to_diff = f"./diff_files/{new_filename}" 
    with open(complete_path_to_diff, "w", encoding="utf-8") as f:
        f.write(diff_text)
    
    return complete_path_to_diff

def has_function_with_min_lines(java_code: str, min_lines: int) -> bool:
    method_pattern = r'(?:public|private|protected|static|\s)*\s*[\w<>[\]]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{'
    
    method_matches = re.finditer(method_pattern, java_code)
    
    for match in method_matches:
        start_pos = match.start()
        brace_count = 1
        current_pos = start_pos + 1
        
        while brace_count > 0 and current_pos < len(java_code):
            if java_code[current_pos] == '{':
                brace_count += 1
            elif java_code[current_pos] == '}':
                brace_count -= 1
            current_pos += 1
            
        if brace_count == 0:
            method_body = java_code[start_pos:current_pos]
            line_count = method_body.count('\n') + 1
            
            if line_count >= min_lines:
                return True
                
    return False

if __name__ == "__main__":

    ini = datetime.now()

    repo_name = 'libgdx/libgdx'
    repos_list = 'repo'
    repo_complete_path = f'{repos_list}/{repo_name.split("/")[-1]}'
    simian_result = 'simian_result'
    os.makedirs(simian_result, exist_ok=True)

    output_diffs = 'diff_files'
    merged_prs = fetch_recent_merged_prs(repo_name, 30)

    remove_files_test = 0
    os.system("rm -rf added_result.csv removed_result.csv")

    for pr in merged_prs:
        clone_and_checkout_pr_base_commit(repo_name, pr["number"], base_dir=repos_list)
        extract_java_diffs_from_pr(pr, output_diffs)
        
        diff_files =  os.listdir(output_diffs)
        if len(diff_files) == 0:
            continue

        for file in diff_files:
            complete_path_to_diffs = f'{output_diffs}/{file}'
            diff_file_content = open(complete_path_to_diffs, 'r').read()

            if re.search(r'\btest\b', diff_file_content.split('\n')[0], re.IGNORECASE):
                remove_files_test += 1
                continue
            
            blocks = extract_valid_blocks(complete_path_to_diffs, 4)
            if len(blocks['removed']) == 0 and len(blocks['added']) == 0:
                continue
            
            info_df = {
                "repo_name": repo_name,
                "repo_link": f"https://github.com/{repo_name}",
                "pr_link": f"https://github.com/{repo_name}/pull/{pr['number']}",
                "pr_diff": pr["diff_url"],
                "pr_number": pr["number"]
            }

            folder_name = repo_name.split('/')[-1] 
            folder_result = {}
            yaml_result = {}
            if len(blocks['removed']) != 0:
                blocks['removed'] = [clean_java_code(block) for block in blocks['removed']]
                blocks = filter_unique_code_blocks(blocks)
                folder_result['removed'] = save_code_blocks('removed', blocks)
                yaml_result['removed'] = f'{simian_result}/removed_{folder_name}_pr{pr["number"]}.yaml'
                execute_simian(folder_result['removed'], repo_complete_path, 'java', yaml_result['removed'])
                info_df["simian_result_removed"] = yaml_result["added"] if yaml_result.get("added") else None
                info_df["block_removed_path"] = folder_result["removed"] if folder_result.get("removed") else None
                info_df["qtd_blocks_removed"] = len(folder_result["removed"]) if folder_result.get("removed") else 0
                extract_blocks_to_csv(yaml_result['removed'], info_df, 'removed')

            if len(blocks['added']) != 0:
                blocks['added'] = [clean_java_code(block) for block in blocks['added']]
                blocks = filter_unique_code_blocks(blocks)
                folder_result['added'] = save_code_blocks('added', blocks)
                yaml_result['added'] = f'{simian_result}/added_{folder_name}_pr{pr["number"]}.yaml'
                execute_simian(folder_result['added'], repo_complete_path, 'java', yaml_result['added'])
                info_df["simian_result_addeed"] = yaml_result["added"] if yaml_result.get("added") else None
                info_df["block_added_path"] = folder_result["added"] if folder_result.get("added") else None
                info_df["qtd_blocks_added"] = len(folder_result["added"]) if folder_result.get("added") else 0
                extract_blocks_to_csv(yaml_result['added'], info_df, 'added')

    execution_time = datetime.now() - ini

    with open("execution_time.txt", "w") as f:
        f.write(f"Time: {execution_time}\n")