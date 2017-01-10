#!/usr/bin/env bash
# coverage and coveralls were put into this script as the execution of multiple commands connected with && failed
coverage run -m unittest discover
coveralls