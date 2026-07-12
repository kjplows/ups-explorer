#!/usr/bin/bash

awk '/^\| /{next} {print};' < <(awk 'NR==1 {next} /^(\|   |[[:space:]])/ {next} {gsub(/\|__/,""); print}' $1)
