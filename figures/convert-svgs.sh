#!/usr/bin/sh

for d in ./sankey*.json; do svg-sankey --margins 0,150 --size 1200,1000 --scale 0.02 "$d" > "svgs/$d.svg"; done
