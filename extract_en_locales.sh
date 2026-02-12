#!/bin/bash

pybabel extract --no-default-keywords -k "_en" -w 99 -o locales/en.pot --ignore-dirs "plugins .*" .