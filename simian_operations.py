import os 
import yaml
def execute_simian(folder1, folder2, extension_language, output_filename):
    '''
    Only works using Java Version >== 17
    '''
    java_jar_command = 'java -jar ./simian/simian-4.0.0.jar'
    options_command = '-formatter=yaml -threshold=4'
    simian_command = f'{java_jar_command} {options_command} "./{folder1}/**.{extension_language}" "./{folder2}/**.{extension_language}" > {output_filename}'

    os.system(simian_command)

    yaml_content = open(output_filename, 'r').read()
    open(output_filename, 'w').write(yaml_content.replace('\\', '/'))


def delete_moved_block_codes(yaml_simian_path):
    yaml_simian_result = open(yaml_simian_path, 'r').read()
    if 'sourceFile' not in yaml_simian_result:
        return

    data = yaml.safe_load(yaml_simian_result.split('---')[-1])
    source_files = set()

    for set_item in data.get('simian', {}).get('checks', []):
        for fingerprint_set in set_item.get('sets', []):
            for block in fingerprint_set.get('blocks', []):
                source_file = block.get('sourceFile')
                if source_file:
                    source_files.add(source_file)

    for source_file in source_files:
        print(f"rm -rf {source_file}")

def filter_unique_code_blocks(removed_blocks, added_blocks):
    removed_blocks_folder = 'removed_blocks'
    os.system(f'rm -rf {removed_blocks_folder}')
    os.makedirs(f'{removed_blocks_folder}')
    for i, r_block in enumerate(removed_blocks):
        open(f'{removed_blocks_folder}/{i}_removed_block.java', 'w').write(r_block)

    added_blocks_folder = 'added_blocks'
    os.system(f'rm -rf {added_blocks_folder}')
    os.makedirs(f'{added_blocks_folder}')
    for i, a_block in enumerate(added_blocks):
        open(f'{added_blocks_folder}/{i}_added_block.java', 'w').write(a_block)

    execute_simian(removed_blocks_folder, added_blocks_folder, 'java')

    delete_moved_block_codes('result.yaml')

    result = {
        'removed': [open(f'{removed_blocks_folder}/{file}', 'r').read() for file in os.listdir(removed_blocks_folder)],
        'added': [open(f'{added_blocks_folder}/{file}', 'r').read() for file in os.listdir(added_blocks_folder)]
    }

    return result
