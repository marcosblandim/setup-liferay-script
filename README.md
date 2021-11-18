# Liferay Setup Script
Script for setting up a Liferay Portal

## What it does?
1. downloads Liferay bundle with the following command
```shell
blade gw initBundle
```
2. gets properties file from the selected environment, sets liferay.home and database url name properties and inserts it inside `bundles`

## Requirements
- python 3
- blade 4.0.9.202107011607
- must be executed from inside a Liferay Gradle Workspace

## Usage
- the following command runs the script with the default values
```shell
python setup.py
```
- use the following command to get help about the script
```shell
python setup.py --help
```

## Future improvements
- make it possible to pass all fields available in wizard setup
- let user choose which database driver to use
