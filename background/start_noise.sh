XP=$1
stdbuf -oL nohup python client.py $XP< /dev/null >> noise.out 2>> noise.err &
