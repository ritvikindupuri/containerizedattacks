#!/bin/bash

echo "Privileged Container Running"
echo "Container ID: $(hostname)"
echo "Capabilities: $(cat /proc/self/status | grep Cap)"
echo ""
echo "This container has:"
echo "- Privileged mode enabled"
echo "- Host filesystem mounted at /host"
echo "- Full access to host resources"
echo ""
echo "Waiting for attacks..."

# Keep container running
tail -f /dev/null
