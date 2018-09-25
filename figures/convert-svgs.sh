#!/usr/bin/sh

for d in with_layout/sankey*.json; do
    svg-sankey --size 1500,1050 --scale 0.02 --position x,y "$d" > "svgs/$(basename $d .json).svg";
done
