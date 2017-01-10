#!/usr/bin/env bash
# coverage and coveralls were put into this script as the execution of multiple commands connected with && failed
coverage run -m unittest discover
COVERALLS_REPO_TOKEN=WRZpqoMXoBs4z7exUYAQ6QFkjpnl5G78Z coveralls