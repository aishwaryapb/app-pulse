#!/bin/bash

echo "Waiting for Kafka to be ready..."

# Wait for Kafka broker to be available
until kafka-topics --bootstrap-server kafka:29092 --list &>/dev/null; do
    echo "Kafka not ready yet, waiting 5 seconds..."
    sleep 5
done

echo "Kafka is ready! Creating topics..."

# Function to create topic if it doesn't exist
create_topic_if_not_exists() {
  local topic_name=$1
  local partitions=$2
  
  # Check if topic exists
  if kafka-topics --bootstrap-server kafka:29092 --list | grep -q "^${topic_name}$"; then
    echo "Topic ${topic_name} already exists"
  else
    echo "Creating topic ${topic_name}..."
    kafka-topics --create \
      --topic ${topic_name} \
      --bootstrap-server kafka:29092 \
      --partitions ${partitions} \
      --replication-factor 1
    
    if [ $? -eq 0 ]; then
      echo "✅ Topic ${topic_name} created successfully"
    else
      echo "❌ Failed to create topic ${topic_name}"
      exit 1
    fi
  fi
}

# Create all topics
create_topic_if_not_exists "api-metrics" 3
create_topic_if_not_exists "system-metrics" 1  
create_topic_if_not_exists "api-errors" 2
create_topic_if_not_exists "ui-errors" 2

echo "🎉 All topics initialized successfully!"