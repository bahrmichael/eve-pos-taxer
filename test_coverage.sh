#!/usr/bin/env bash
# coverage and coveralls were put into this script as the execution of multiple commands connected with && failed
git clone https://github.com/bahrmichael/eve-pos-taxer eve-pos-taxer
cd eve-pos-taxer
coverage run -m unittest discover
COVERALLS_REPO_TOKEN=WRZpqoMXoBs4z7exUYAQ6QFkjpnl5G78Z coveralls