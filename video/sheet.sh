#!/bin/zsh
# Render a contact sheet of frames: ./sheet.sh name f1 f2 ...
name=$1; shift
mkdir -p out/sheet/$name
for f in "$@"; do
  npx remotion still RackBotPitch out/sheet/$name/$(printf %05d $f).png --frame=$f --gl=angle --scale=0.5 >/dev/null 2>&1 || echo "fail $f"
done
ffmpeg -y -loglevel error -pattern_type glob -i "out/sheet/$name/*.png" -vf "scale=640:-1,tile=3x$(( ($# + 2) / 3 ))" -frames:v 1 out/sheet/$name.png
echo out/sheet/$name.png
