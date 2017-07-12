
VBoxManage modifyvm OVS --intnet2 hadoop1 --nic2 intnet --nicpromisc2 allow-all
VBoxManage modifyvm OVS --intnet3 hadoop2 --nic3 intnet --nicpromisc3 allow-all
VBoxManage modifyvm OVS --intnet4 hadoop3 --nic4 intnet --nicpromisc4 allow-all
VBoxManage modifyvm OVS --intnet5 hadoop4 --nic5 intnet --nicpromisc5 allow-all
VBoxManage modifyvm OVS --intnet6 hadoop5 --nic6 intnet --nicpromisc6 allow-all
#VBoxManage clonevm Hadoop2 --name Hadoop5 --register
#VBoxManage modifyvm Hadoop5 --intnet2 hadoop5 --nic2 intnet
