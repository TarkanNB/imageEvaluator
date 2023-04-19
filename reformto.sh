#!/usr/bin/env bash
# Renames all images from {sample}_{type}.png to {sample}___{type}.png
for pic in *.png; do
    mv "$pic" "${pic%_*}__${pic##*_}"
done