#!/bin/bash

export string=WORDLIKE

for (( i = 0; i < ${#string}; i++ )); do
  char="${string:i:1}"
  convert -size 1024x1024 xc:black -font ~/.fonts/Birbaslo.ttf -pointsize 800 -gravity center -fill white -annotate +0+0 "${char}" png:- | convert - -blur 0x8  letters/${char}.png
done
