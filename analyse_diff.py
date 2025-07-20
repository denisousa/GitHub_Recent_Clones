from github import Github, Auth
from dotenv import load_dotenv
from lsh_operation import filter_unique_code_blocks
from github_operations import checkout_repo_commit_by_index, download_java_files_from_github
from simian_operations import execute_simian
from yaml_operations import extract_blocks_to_csv
import random
import string
import os
import re

load_dotenv()
token = os.getenv("GH_TOKEN")

def save_code_blocks(blocks: dict, base_dir: str = "."):
    folder_path_result = []
    for key in ['added', 'removed']:
        block_list = blocks.get(key, [])
        os.makedirs('blocks', exist_ok=True)

        hash_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        folder_name = f"blocks/blocks_{key}_{hash_suffix}"
        folder_path = os.path.join(base_dir, folder_name)

        folder_path_result.append(folder_path)
        
        os.system(f'rm -rf "{folder_path}"')
        os.makedirs(folder_path)

        for i, code in enumerate(block_list, start=1):
            file_path = os.path.join(folder_path, f"block_{i}.java")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

        print(f"Saved {len(block_list)} blocks to '{folder_name}'")

    return folder_path_result

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

repo_name = 'Stirling-Tools/Stirling-PDF'
checkout_repo_commit_by_index(
    repo_name=repo_name,
    commit_index=80,
)

auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo(repo_name)

commits = repo.get_commits()
current_commit = commits[80]
previous_commit = commits[90]

os.system('rm -rf diff_files')
os.makedirs('diff_files')

diff = repo.compare(previous_commit.sha, current_commit.sha)
diff_java_files = [file for file in diff.files if file.filename.endswith(".java")]

add_blocks_list = []
removed_blocks_list = []

os.system("rm -rf blocks_added.csv")
os.system("rm -rf blocks_removed.csv")

remove_files_test = 0
for file in diff_java_files:
    if re.search(r'\btest\b', file.filename, re.IGNORECASE):
        remove_files_test += 1

    complete_path_to_diffs = generate_diff_file(file, f"{file.filename}.diff")
    print(f"Filename: {file.filename}")
    print(f"Changes:\n{file.patch}")
    
    blocks = extract_valid_blocks(complete_path_to_diffs, 4)
    blocks['removed'] = [clean_java_code(block) for block in blocks['removed']]
    blocks['added'] = [clean_java_code(block) for block in blocks['added']]
    blocks = filter_unique_code_blocks(blocks)
    folder_result = save_code_blocks(blocks)

    folder_name = repo_name.split('/')[-1] 
    added_yaml_result = f'added_{folder_name}.yaml'
    removed_yaml_result = f'removed_{folder_name}.yaml'
    
    execute_simian(folder_result[0], folder_name, 'java', added_yaml_result)
    execute_simian(folder_result[1], folder_name, 'java', removed_yaml_result)

    extract_blocks_to_csv(added_yaml_result, "blocks_added.csv", file.filename)
    extract_blocks_to_csv(removed_yaml_result, "blocks_removed.csv", file.filename)

