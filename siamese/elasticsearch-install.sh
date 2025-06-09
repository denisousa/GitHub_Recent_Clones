#!/bin/bash

# Name of the Elasticsearch folder
ELASTICSEARCH_DIR="siamese/elasticsearch-2.2.0"

# Check if the folder already exists
if [ -d "$ELASTICSEARCH_DIR" ]; then
  echo "Directory $ELASTICSEARCH_DIR already exists. Skipping download and configuration."
else
  # Download Elasticsearch
  wget https://download.elasticsearch.org/elasticsearch/release/org/elasticsearch/distribution/tar/elasticsearch/2.2.0/elasticsearch-2.2.0.tar.gz &&
  tar -xvf elasticsearch-2.2.0.tar.gz &&
  mv -i elasticsearch-2.2.0 siamese/elasticsearch-2.2.0/ &&
  rm -rf elasticsearch-2.2.0.tar.gz
  rm -rf elasticsearch-2.2.0 


  CONFIG_FILE="$ELASTICSEARCH_DIR/config/elasticsearch.yml"

  # Check if the configuration file exists
  if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found at $CONFIG_FILE"
    exit 1
  fi

  # Append configuration lines if not already present
  grep -qxF "cluster.name: stackoverflow" "$CONFIG_FILE" || echo "cluster.name: stackoverflow" >> "$CONFIG_FILE"
  grep -qxF "index.query.bool.max_clause_count: 4096" "$CONFIG_FILE" || echo "index.query.bool.max_clause_count: 4096" >> "$CONFIG_FILE"

  echo "Configuration successfully added to $CONFIG_FILE"
fi

# Kill process running in 9300 port
PID=$(lsof -ti tcp:9300)

if [ -n "$PID" ]; then
  echo "Killing process on port 9300 (PID: $PID)..."
  kill -9 $PID
  echo "Process killed."
else
  echo "No process is using port 9300."
fi

# Start Elasticsearch in the background
./$ELASTICSEARCH_DIR/bin/elasticsearch -d
echo "Elasticsearch running in the background"
