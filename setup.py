import logging
import subprocess
import configparser
import argparse
import sys
import pathlib


DEFAULT_LOG_LEVEL = 'INFO'
PROPERTIES_FILENAME = 'portal-ext.properties'
BLADE_MIN_VERSION = (4, 0, 9)

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
parser = argparse.ArgumentParser(
    description='Setup Liferay gradle workspace.', epilog=f'for the project docs, go to {github_url}')
parser.add_argument('-l', '--log-level', default=DEFAULT_LOG_LEVEL, type=str.upper,
                    choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'], help='set log level')
parser.add_argument('-d', '--database', default='lportal',
                    help='database name')
parser.add_argument('-e', '--environment', default=WIZ_ENV, type=str.lower, choices=[
                    'common', 'dev', 'docker', 'local', 'prod', 'uat', WIZ_ENV], help='portal environment')
parser.add_argument('workspace_path', nargs='?', default='.',
                    type=pathlib.Path, help='path to a Liferay Gradle Workspace')

args = parser.parse_args()

database_name = args.database
portal_environment = args.environment
log_lever = args.log_level
workspace_path = args.workspace_path.resolve()

# config logging
numeric_level = getattr(logging, log_lever.upper(), DEFAULT_LOG_LEVEL)
logging.basicConfig(format='%(levelname)s: %(message)s', level=numeric_level)

# parse paths
if not workspace_path.is_dir():
    logging.error(f'invalid workspace path \'{workspace_path}\', exiting')
    sys.exit(1)

bundles_path = workspace_path / 'bundles'
bundles_properties_file_path = bundles_path / PROPERTIES_FILENAME


def validate_versions():
    blade_version_process = subprocess.run(
        'blade version', stdout=subprocess.PIPE,
        cwd=workspace_path, shell=True)

    validate_return_code(blade_version_process.returncode,
                         'couldn\'t validate blade\'s version, exiting')

    blade_version = blade_version_process.stdout.decode('utf-8')

    blade_version_str_list = blade_version.split()[-1].split('.')
    blade_version_int_tuple = tuple(int(str_version)
                                    for str_version in blade_version_str_list)

    return blade_version_int_tuple >= BLADE_MIN_VERSION


def have_bundles():
    return bundles_path.is_dir()


def create_bundles():
    process = subprocess.run('blade gw initBundle',
                             cwd=workspace_path, shell=True)
    validate_return_code(process.returncode,
                         'couldn\'t create bundle, exiting')


def validate():
    if not validate_versions():
        valid_blade_version = '.'.join(str(version_unit)
                                       for version_unit in BLADE_MIN_VERSION)
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
        properties_file_path = bundles_path / 'configs' / \
            portal_environment / PROPERTIES_FILENAME

        if not properties_file_path.is_file():
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
               bundles_path.as_posix())

    # TODO: improve database naming
    config.set(PLACEHOLDER_SECTION_NAME, 'jdbc.default.url',
               f'jdbc:postgresql://localhost:5432/{database_name}')

    return config


def set_properties(config):
    logging.info('inserting properties file inside bundles folder')
    logging.debug(f'bundles folder is located at {bundles_path}')

    with open(bundles_properties_file_path, 'w+') as bundles_properties_file:
        config.write(bundles_properties_file)
    with open(bundles_properties_file_path, 'r') as fi:
        properties_file_content = fi.read().splitlines(True)
    with open(bundles_properties_file_path, 'w') as fo:
        fo.writelines(properties_file_content[1:])  # remove section


def validate_return_code(return_code, error_msg):
    if return_code != 0:
        logging.error(error_msg)
        sys.exit(return_code)


def main():
    validate()
    handle_bundles()

    config = get_properties()
    set_properties(config)


if __name__ == '__main__':
    main()
