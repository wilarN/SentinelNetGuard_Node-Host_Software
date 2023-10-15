#!/bin/bash

CUSTOM_COMMAND="sng" # sng for SentinelNetGuard

show_help() {
  echo "Usage: $CUSTOM_COMMAND [--start]"
  echo "Options:"
  echo "  --start   Start the node."
}

case "$1" in
  --start)
    echo "Starting the SentinelNetGuard Node..."
    /opt/SentinelNetGuard/main.py
    ;;
  *)
    show_help
    ;;
esac