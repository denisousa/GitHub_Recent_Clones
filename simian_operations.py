import os 


def execute_simian(folder, extension_language):
    '''
    Only works using Java Version >== 17
    '''
    java_jar_command = 'java -jar ./simian/simian-4.0.0.jar'
    options_command = '-formatter=yaml -threshold=4'
    simian_command = f'{java_jar_command} {options_command} "./{folder}/**.{extension_language}" > result.yaml'

    os.system(simian_command)

    yaml_content = open('result.yaml', 'r').read()
    open('result.yaml', 'w').write(yaml_content.replace('\\', '/'))
