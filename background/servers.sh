for port in 10010
do
    stdbuf -oL nohup python server.py $port < /dev/null > server$port.out 2> server$port.err &
done
