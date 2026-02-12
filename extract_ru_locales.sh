#!/bin/bash

pybabel extract --no-default-keywords -k "_ translate" -w 99 -o locales/ru.pot --ignore-dirs "plugins .*" .