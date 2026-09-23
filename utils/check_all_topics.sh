#!/bin/bash
# Check all ROS2 topics and save results to a file
# Run with: ./check_all_topics.sh

OUTPUT_FILE="topic_check_$(date +%Y%m%d_%H%M%S).txt"
TIMEOUT=3  # seconds to wait for each topic

echo "Checking all ROS2 topics (timeout: ${TIMEOUT}s per topic)"
echo "Output will be saved to: $OUTPUT_FILE"
echo ""

# Get list of all topics
TOPICS=$(ros2 topic list)

{
    echo "=============================================="
    echo "ROS2 Topic Check - $(date)"
    echo "=============================================="
    echo ""

    for topic in $TOPICS; do
        echo "----------------------------------------------"
        echo "TOPIC: $topic"
        echo "----------------------------------------------"

        # Get topic info (type, publishers, subscribers)
        echo "[INFO]"
        ros2 topic info "$topic" 2>&1
        echo ""

        # Try to get one message with timeout
        echo "[DATA] (timeout: ${TIMEOUT}s)"
        timeout $TIMEOUT ros2 topic echo "$topic" --once 2>&1 || echo "(no data received within ${TIMEOUT}s)"
        echo ""
    done

    echo "=============================================="
    echo "Check completed: $(date)"
    echo "=============================================="

} | tee "$OUTPUT_FILE"

echo ""
echo "Results saved to: $OUTPUT_FILE"
