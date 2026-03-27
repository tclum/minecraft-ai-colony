#!/bin/zsh

cd "$(dirname "$0")"

JAR=$(ls paper*.jar | head -n 1)

if [[ -z "$JAR" ]]; then
  echo "No Paper jar found!"
  exit 1
fi

if [[ "$1" == "nogui" ]]; then
  echo "Starting $JAR (nogui)..."
  java -Xms4G -Xmx8G -jar "$JAR" nogui
else
  echo "Starting $JAR (GUI)..."
  java -Xms4G -Xmx8G -jar "$JAR"
fi