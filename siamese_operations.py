'''
Obter todos os clones de um projeto

1. Indexar projeto (Método)
2. Buscar clones no mesmo projeto (Método)
3. Ler arquivo de resultados
4. Armazenar em uma pasta cada par de bloco de código no diretório X
5. Indexar cada par de bloco de código do diretório X


'''
import re
import os
import subprocess
from time import sleep
from dotenv import load_dotenv
import requests

def elasticsearch_is_running() -> bool:
    try:
        result = subprocess.run(
            ['curl', 'http://localhost:9300'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print("Elasticsearch is running. Response:")
        print(result.stdout)
        return True

    except subprocess.CalledProcessError as e:
        print("Error checking Elasticsearch:")
        print(e.stderr)
        return False

def execute_elasticsearch():
    subprocess.run(f'chmod +x {elasticsearch_sh_path} && {elasticsearch_sh_path}', shell=True, check=True)
    # subprocess.run(f'{elasticsearch_sh_path}', shell=True, check=True)
    if not elasticsearch_is_running():
        command_execute = f'{elasticsearch_path}/bin/elasticsearch -d'
        process = subprocess.Popen(command_execute, shell=True, stdout=subprocess.PIPE)
        process.wait()
        sleep(3)

def update_config(project_complete_path: str, command: str, config_path: str) -> None:
    with open(template_config_path, 'r') as template_file:
        config_content = template_file.read()
    config_content = config_content.replace('inputFolder=', f'inputFolder={project_complete_path}')
    config_content = config_content.replace('command=', f'command={command}')
    
    with open(config_path, 'w') as config_file:
        config_file.write(config_content)


def run_siamese(jar_path: str, config_path: str) -> None:
    try:
        command = f'java -jar {jar_path} -cf {config_path}'
        process = subprocess.Popen(command,
                                   shell=True,
                                   stdin=None,
                                   stdout=None,
                                   stderr=None,
                                   close_fds=True)
        process.wait()

    except subprocess.CalledProcessError as e:
        print(f'Error to execute {config_path}: {e}')



if __name__ == '__main__':
    src_siamese_path = 'siamese'
    siamese_path = f'{src_siamese_path}/siamese-0.0.6-SNAPSHOT.jar'
    template_config_path = f'{src_siamese_path}/template-config.properties'
    index_config_path = f'{src_siamese_path}/index-config.properties'
    search_config_path = f'{src_siamese_path}/search-config.properties'
    elasticsearch_path = f'./{src_siamese_path}/elasticsearch-2.2.0'
    elasticsearch_sh_path = f'./{src_siamese_path}/elasticsearch-install.sh'
    project_complete_path = '/home/denis/GitHub_Recent_Clones/Stirling-PDF'

    update_config(project_complete_path, 'index', index_config_path)
    update_config(project_complete_path, 'search', search_config_path)

    execute_elasticsearch()
    run_siamese(siamese_path, index_config_path)
    run_siamese(siamese_path, search_config_path)