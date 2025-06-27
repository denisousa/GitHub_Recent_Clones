from github import Github
from dotenv import load_dotenv
from simian_operations import execute_simian
import difflib
import re
import os

def filter_unique_code_blocks(removed_blocks, added_blocks, similarity_threshold=0.5):
    to_remove_from_removed = set()
    to_remove_from_added = set()

    for i, r_block in enumerate(removed_blocks):
        for j, a_block in enumerate(added_blocks):
            ratio = difflib.SequenceMatcher(None, r_block.strip(), a_block.strip()).ratio()
            if ratio >= similarity_threshold:
                to_remove_from_removed.add(i)
                to_remove_from_added.add(j)

    result = {
        'removed': [block for i, block in enumerate(removed_blocks) if i not in to_remove_from_removed],
        'added': [block for j, block in enumerate(added_blocks) if j not in to_remove_from_added]
    }

    return result


def extract_valid_blocks(diff_file_path, min_block_size):
    """
    Extracts changed blocks from a diff file where '-' lines are followed by '+' lines.
    Returns a list of dictionaries with 'removed' and 'added' code blocks.
    """

    lines = open(diff_file_path, encoding='utf-8').readlines()
    code_block = {'added': [], 'removed': []}

    valid_block = []
    positive_block = None
    for line in lines[3:]:
        
        # Case vazio
        if len(valid_block) == 0:
            if line.startswith('-'):
                valid_block.append(line)
                positive_block = False
            if line.startswith('+'):
                valid_block.append(line)
                positive_block = True
            continue

        # Case -/+ or +/-
        if (line[0] == '-' and positive_block) or (line[0] == '+' and not positive_block):
            if has_function_with_min_lines(''.join(valid_block), min_block_size):
                if line[0] == '-':
                    code_block['removed'].append(''.join(valid_block))
                else:
                    code_block['added'].append(''.join(valid_block))

            if line.startswith('-'):
                positive_block = False
            else:
                positive_block = True

            valid_block = [line]           

        # Case -/'' or +/''
        if (line[0] != '-' and line[0] != '+'):
            if has_function_with_min_lines(''.join(valid_block), min_block_size):
                if line[0] == '-':
                    code_block['removed'].append(''.join(valid_block))
                else:
                    code_block['added'].append(''.join(valid_block))

            positive_block = None
            valid_block = []     

        # Case -/- or +/+
        if (line[0] == '-' and not positive_block) or (line[0] == '+' and positive_block):
            valid_block.append(line)
        
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

def get_add_blocks(filename):
    pass

def get_removed_blocks():
    pass

def has_function_with_min_lines(java_code: str, min_lines: int) -> bool:
    # Pattern to match Java method declarations
    method_pattern = r'(?:public|private|protected|static|\s)*\s*[\w<>[\]]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{'
    
    # Find all method declarations
    method_matches = re.finditer(method_pattern, java_code)
    
    for match in method_matches:
        start_pos = match.start()
        # Find the corresponding closing brace
        brace_count = 1
        current_pos = start_pos + 1
        
        while brace_count > 0 and current_pos < len(java_code):
            if java_code[current_pos] == '{':
                brace_count += 1
            elif java_code[current_pos] == '}':
                brace_count -= 1
            current_pos += 1
            
        if brace_count == 0:
            # Count lines in the method body
            method_body = java_code[start_pos:current_pos]
            line_count = method_body.count('\n') + 1
            
            if line_count >= min_lines:
                return True
                
    return False

load_dotenv()

token = os.getenv("GH_TOKEN")
g = Github(token)

repo = g.get_repo('Stirling-Tools/Stirling-PDF')

commits = repo.get_commits()
current_commit = commits[0]
previous_commit = commits[70]

os.system('rm -rf diff_files')
if not os.path.exists('diff_files'):
    os.makedirs('diff_files')

diff = repo.compare(previous_commit.sha, current_commit.sha)
diff_java_files = [file for file in diff.files if file.filename.endswith(".java")]

add_blocks_list = []
removed_blocks_list = []

remove_files_test = 0

# execute_simian('diff_files', 'diff')

for file in diff_java_files:
    if re.search(r'\btest\b', file.filename, re.IGNORECASE):
        remove_files_test += 1

    complete_path_to_diffs = generate_diff_file(file, f"{file.filename}.diff")
    print(f"Filename: {file.filename}")
    print(f"Changes:\n{file.patch}")
    
    blocks = extract_valid_blocks(complete_path_to_diffs, 8)
    blocks = filter_unique_code_blocks(blocks['removed'], blocks['added'])
    if blocks['removed'] or blocks['added']:
        [print(f'added block: {i}\n', block, "*******************************") for i, block in enumerate(blocks['removed'])]
        print('============================')

        [print(f'removed block: {i}\n', block, "*******************************") for i, block in enumerate(blocks['added'])]
        print('============================')

    # add_blocks = get_add_blocks(complete_path_to_diff)
    # if add_blocks:
    #     add_blocks_list.append({complete_path_to_diff: add_blocks})

    # removed_blocks = get_removed_blocks(complete_path_to_diff) 
    # if removed_blocks:
    #     removed_blocks_list.remove({complete_path_to_diff: removed_blocks})

print(f'REMOVED FILES TEST: {remove_files_test}')