echo "Prepare switch:"
echo "==============="
sudo  service  openvswitch-switch restart
sudo ovs-ofctl -O OpenFlow13 dump-flows br-int
for i in "enp0s8" "enp0s9" "enp0s10" "enp0s16"
do
  echo ""
  echo "Setup $i:"
  echo "============="
  sudo ovs-vsctl set interface $i ingress_policing_rate=0
  sudo ovs-vsctl set interface $i ingress_policing_burst=0
  sudo ovs-vsctl list interface $i
done

