#!/bin/bash

pybabel extract --no-default-keywords -k "_ _en translate" -w 99 -o locales/all.pot --ignore-dirs "plugins .*" .