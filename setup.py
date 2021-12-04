import logging
import subprocess
import configparser
import argparse
import sys
import os


DEFAULT_LOG_LEVEL = 'INFO'
PROPERTIES_FILENAME = 'portal-ext.properties'
SCRIPT_BLADE_VERSION = (4, 0, 9)

PLACEHOLDER_SECTION_NAME = 'placeholder'
WIZ_ENV = 'wiz'
WIZ_PROPERTIES = '''include-and-override=portal-developer.properties

admin.email.from.address=test@liferay.com
admin.email.from.name=Test Test
company.default.locale=en_US
company.default.time.zone=UTC
company.default.web.id=liferay.com
default.admin.email.address.prefix=test

jdbc.default.driverClassName=org.postgresql.Driver
jdbc.default.password=postgres
jdbc.default.url=jdbc:postgresql://localhost:5432/lportal
jdbc.default.username=postgres

#liferay.home=
setup.wizard.enabled=false'''


# parse args
github_url = 'https://github.com/marcosblandim/setup-liferay-script/'
parser = argparse.ArgumentParser(description='Setup Liferay gradle workspace.',
                                 epilog=f'for the project docs, go to {github_url}')
parser.add_argument('-l', '--log-level', default=DEFAULT_LOG_LEVEL,
                    choices=['CRITICAL', 'ERROR', 'WARNING',
                             'INFO', 'DEBUG', 'NOTSET'],
                    type=str.upper, help='set log level')
parser.add_argument('-d', '--database', default='lportal',
                    help='database name')
parser.add_argument('-e', '--environment', default=WIZ_ENV,
                    choices=['common', 'dev', 'docker',
                             'local', 'prod', 'uat', WIZ_ENV],
                    help='portal environment')

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


def validate_versions():
    blade_version_bytes = subprocess.run(
        'blade version', stdout=subprocess.PIPE, cwd=this_file_folder_path)
    blade_version = blade_version_bytes.stdout.decode('utf-8')

    blade_version_str_list = blade_version.split()[-1].split('.')
    blade_version_int_tuple = tuple(int(str_version)
                                    for str_version in blade_version_str_list)

    return blade_version_int_tuple >= SCRIPT_BLADE_VERSION


def have_bundles():
    return os.path.isdir(bundles_path)


def create_bundles():
    subprocess.run('blade gw initBundle', cwd=this_file_folder_path)

def validate():
    if not validate_versions():
        valid_blade_version = '.'.join(str(version_unit)
                                       for version_unit in SCRIPT_BLADE_VERSION)
        logging.error(
            f'invalid blade version, must be greater than {valid_blade_version}. Run \'blade update\'')
        sys.exit(1)

def handle_bundles():
    if not have_bundles():
        logging.info('creating bundles folder')
        create_bundles()
    else:
        logging.info('bundles folder already exists')

def get_properties():
    if portal_environment != WIZ_ENV:
        properties_file_path = os.path.join(
            this_file_folder_path, 'configs', portal_environment, PROPERTIES_FILENAME)
        properties_file_exists = os.path.isfile(properties_file_path)

        if not properties_file_exists:
            logging.error(f'{properties_file_path} file do not exists')
            sys.exit(1)

        with open(properties_file_path, 'r') as f:
            properties = f.read()
        
        logging.info(
            f'reading properties file from \'{portal_environment}\' environment')
        logging.debug(f'properties file is located at {properties_file_path}')

    else:
        properties = WIZ_PROPERTIES
        logging.info(
            f'using wizard\'s default properties')

    properties_with_section = f'[{PLACEHOLDER_SECTION_NAME}]\n' + properties
    
    config = configparser.ConfigParser()
    config.optionxform = str  # set case insensitive

    config.read_string(properties_with_section)
    config.set(PLACEHOLDER_SECTION_NAME, 'liferay.home',
               bundles_path.replace('\\', '/'))

    # TODO: improve database naming
    config.set(PLACEHOLDER_SECTION_NAME, 'jdbc.default.url',
               f'jdbc:postgresql://localhost:5432/{database_name}')

    return config

def set_properties(config):
    logging.info('inserting properties file inside bundles folder')
    logging.debug(f'bundles folder is located at {bundles_path}')
    bundles_properties_file_path = os.path.join(
        bundles_path, PROPERTIES_FILENAME)
    with open(bundles_properties_file_path, 'w+') as bundles_properties_file:
        config.write(bundles_properties_file)
    with open(bundles_properties_file_path, 'r') as fi:
        properties_file_content = fi.read().splitlines(True)
    with open(bundles_properties_file_path, 'w') as fo:
        fo.writelines(properties_file_content[1:]) # remove section


if __name__ == '__main__':

    validate()
    handle_bundles()

    config = get_properties()
    set_properties(config)
