for port in {10011..10013}
do
  echo "start $port"
  python server.py $port&
done

