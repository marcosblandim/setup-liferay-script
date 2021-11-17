import logging
import subprocess
import configparser
import argparse
import sys
import os


DEFAULT_LOG_LEVEL = 'INFO'
PROPERTIES_FILENAME = 'portal-ext.properties'

# get args
parser = argparse.ArgumentParser(description='Setup Liferay gradle workspace.')
parser.add_argument('-d', '--database', default='lportal', help='database name')
parser.add_argument('-e', '--environment', default='dev',
                    choices=['common', 'dev', 'docker', 'local', 'prod','uat'],
                    help='portal environment')
parser.add_argument('-l', '--log-level', default=DEFAULT_LOG_LEVEL,
                    choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'],
                    type= str.upper,
                              help='set log level')

args = parser.parse_args()

database_name = args.database
portal_environment = args.environment
log_lever = args.log_level

# config logging
numeric_level = getattr(logging, log_lever.upper(), DEFAULT_LOG_LEVEL)
logging.basicConfig(format='%(levelname)s: %(message)s', level=numeric_level)

# get this file folder path
if sys.version_info >= (3, 9):
    this_file_folder_path = os.path.split(__file__)[0]
else:
    this_file_folder_path = os.path.dirname(os.path.abspath(__file__))

bundles_path = os.path.join(this_file_folder_path, 'bundles')


def have_bundles():
    return os.path.isdir(bundles_path)

def create_bundles():
    subprocess.run('blade gw initBundle', cwd=this_file_folder_path)


if __name__ == '__main__':
    if not have_bundles():
        create_bundles()

    properties_file_path = os.path.join(this_file_folder_path, 'configs', portal_environment, PROPERTIES_FILENAME)
    properties_file_exists = os.path.isfile(properties_file_path)

    if not properties_file_exists:
        logging.error(f'{properties_file_path} file do not exists')
        sys.exit(1)

    placeholder_section_name = 'placeholder'
    config = configparser.ConfigParser()
    with open(properties_file_path, 'r') as f:
        properties_with_section = f'[{placeholder_section_name}]\n' + f.read()

    config.read_string(properties_with_section)

    # TODO: see if this affects linux
    config.set(placeholder_section_name, 'liferay.home', bundles_path.replace('\\','/'))

    # TODO: improve database naming
    config.set(placeholder_section_name, 'jdbc.default.url', f'jdbc:postgresql://localhost:5432/{database_name}') #

    bundles_properties_file_path = os.path.join(bundles_path, PROPERTIES_FILENAME)
    with open(bundles_properties_file_path, 'w+') as bundles_properties_file:
        config.write(bundles_properties_file)
    with open(bundles_properties_file_path, 'r') as fi:
        properties_file_content = fi.read().splitlines(True)
    with open(bundles_properties_file_path, 'w') as fo:
        fo.writelines(properties_file_content[1:])
