DATE="$(date +%d-%m-%yT%H:%M:%S%Z)"
MONTH="$(date +%m-%y)"
DAY="$(date +%m-%d)"

mkdir -p logs/$MONTH/$DAY

python3 ./ucrm_api.py > ./logs/"$MONTH"/"$DAY"/sync_"$DATE".log
