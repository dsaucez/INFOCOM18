export ryu_c=$1
export ryu_random=$2
export ryu_XP=$3

stdbuf -oL nohup ryu-manager ovs/controller.py < /dev/null > controller.out 2> controller.err &
