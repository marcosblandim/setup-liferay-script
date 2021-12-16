# Liferay Setup Script
Script for setting up a Liferay Portal

## What it does?
1. downloads Liferay bundle (if it doesn't exists yet) with the following command
```shell
blade gw initBundle
```
2. gets the properties from the selected environment, sets liferay.home and database url name properties and inserts it in a `portal-ext.properties` file inside `bundles` folder

## Requirements
- python 3
- blade 4.0.9.202107011607
- must be executed from the root of a Liferay Gradle Workspace

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
- make it possible to pass all fields available in wizard setup, even the database driver (see portal-impl properties file)
  - have default value for all fields
- improve docs
  - [usage](#usage)
- make it works for many versions (currently only works on 7.3)
- add the option to create the database and the portal in a docker
- improve logging
- external bundle option -> use bundle located outside the workspace
    - validate `liferay.workspace.home.dir` inside `gradle.properties` file
- check if blade gw initBundle executed correctly
- flag for reseting `bundles` folder
