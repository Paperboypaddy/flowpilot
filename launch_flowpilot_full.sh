set -e
source ./.env

export LD_LIBRARY_PATH=/system/vendor/lib64:$LD_LIBRARY_PATH

export WIDE_ROAD_CAMERA_SOURCE="selfdrive/assets/tmp" # no affect on android
export ROAD_CAMERA_SOURCE="selfdrive/assets/tmp" # no affect on android
export USE_GPU="0" # no affect on android, gpu always used on android
export PASSIVE="0"
export NOSENSOR="1"
#export MSGQ="1"
#export USE_PARAMS_NATIVE="1"
export ZMQ_MESSAGING_PROTOCOL="TCP" # TCP, INTER_PROCESS, SHARED_MEMORY

#export DISCOVERABLE_PUBLISHERS="1" # if enabled, other devices on same network can access sup/pub data.
#export DEVICE_ADDR="127.0.0.1" # connect to external device running flowpilot over same network. useful for livestreaming.

export SIMULATION="0"
export FINGERPRINT="HYUNDAI IONIQ HYBRID 2017-2019"

## android specific ##
export USE_SNPE="1" # only works for snapdragon devices.

## get all cars
mkdir -p /sdcard/flowpilot
cat selfdrive/car/*/values.py|grep '= "'|grep -v ':'|awk -F'"' '{print $(NF-1)}' | sort > /sdcard/flowpilot/allcars.txt
sed -i '1s/^/--Select Cars--\n/' /sdcard/flowpilot/allcars.txt

if ! command -v tmux &> /dev/null
then
    echo "tmux could not be found, installing.."
    sudo apt-get update
    sudo apt-get install tmux
    echo "set -g mouse on" >> ~/.tmux.conf # enable mouse scrolling in tmux
    echo "set -g remain-on-exit on" >> ~/.tmux.conf # retain tmux session on ctrl + c
fi

if pgrep -x "flowinit" > /dev/null
    then
        echo "another instance of flowinit is already running"
        exit
    else
        # start a tmux pane
        scons -j$(nproc) && flowinit
        # tmux new-session -d -s "flowpilot" "scons && flowinit"
        # tmux attach -t flowpilot
fi

while true; do sleep 1; done
