#!/usr/bin/env bash

#set -e
#set -o xtrace

# Variables
LOG_GROUP_NAME="/example/basic/app2"
LOG_STREAM_NAME="1727420166"
LOG_FILE="web_server_logs.log"

# Initialize the sequence token variable
SEQUENCE_TOKEN=""

# Function to send log events
send_log_events() {
  local timestamp=$1
  local message=$2
  echo $message > /dev/tty
  
  # Create a JSON object
  json=$(jq -c -n --arg ts "$timestamp" --arg msg "$message" '[{"timestamp": ($ts|tonumber), "message": $msg}]')

  echo "Sending JSON: $json" > /dev/tty  # Debugging line

  if [ -z "$SEQUENCE_TOKEN" ]; then
    echo "First log event, no sequence token available."
    SEQUENCE_TOKEN=$(aws logs put-log-events \
    --log-group-name "$LOG_GROUP_NAME" \
    --log-stream-name "$LOG_STREAM_NAME" \
    --log-events "$json" \
    --query nextSequenceToken \
    --output text)
  else
    echo "Using sequence token: $SEQUENCE_TOKEN"
    SEQUENCE_TOKEN=$(aws logs put-log-events \
    --log-group-name "$LOG_GROUP_NAME" \
    --log-stream-name "$LOG_STREAM_NAME" \
    --log-events "$json" \
    --sequence-token "$SEQUENCE_TOKEN" \
    --query nextSequenceToken \
    --output text)
  fi

  # Check for any errors
  if [ $? -ne 0 ]; then
      echo "Error sending log event. Please check the AWS CLI output."
  fi
}

convert_to_iso() {
    # Input date string
    local date_str="$1"

    # Extract parts of the date
    local day=$(echo "$date_str" | awk -F'[/: ]' '{print $1}')
    local month=$(echo "$date_str" | awk -F'[/: ]' '{print $2}')
    local year=$(echo "$date_str" | awk -F'[/: ]' '{print $3}')
    local time=$(echo "$date_str" | awk -F'[/: ]' '{print $4 ":" $5 ":" $6}')
    local timezone=$(echo "$date_str" | awk -F'+' '{print $2}')

    # Convert month to a number
    case $month in
        Jan) month_num="01" ;;
        Feb) month_num="02" ;;
        Mar) month_num="03" ;;
        Apr) month_num="04" ;;
        May) month_num="05" ;;
        Jun) month_num="06" ;;
        Jul) month_num="07" ;;
        Aug) month_num="08" ;;
        Sep) month_num="09" ;;
        Oct) month_num="10" ;;
        Nov) month_num="11" ;;
        Dec) month_num="12" ;;
    esac

    # Format the date as ISO 8601
    local iso_date="${year}-${month_num}-${day}T${time} +${timezone}"

    # Print the result
    echo "$iso_date"
}

# Read log file and send logs to CloudWatch
while IFS= read -r line; do
  original_datetime=$(echo "$line" | awk '{print $4 " " $5}' | sed 's/\[//;s/\]//')
  iso_datetime=$(convert_to_iso "$original_datetime")
  timestamp=$(date --date="$iso_datetime" +%s%3N)
  send_log_events "$timestamp" "$line"
done < "$LOG_FILE"

echo "Logs have been sent to CloudWatch Log Stream $LOG_STREAM_NAME in Log Group $LOG_GROUP_NAME"
