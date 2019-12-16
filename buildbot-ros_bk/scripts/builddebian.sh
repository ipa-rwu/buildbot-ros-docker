#!/bin/bash
cd /tmp
#rosdep db
#rosdep install --from-paths src --ignore-src -r -y
source /opt/ros/kinetic/setup.bash
sh -c 'echo "yaml file:///home/package/private.yaml" >> /etc/ros/rosdep/sources.list.d/20-default.list'
rosdep update
rosdep db
missing=`dpkg-checkbuilddeps 2>&1 | sed 's/dpkg-checkbuilddeps:\serror:\sUnmet build dependencies: //g' | sed 's/[\(][^)]*[\)] //g'`
echo "missing : $missing"
apt-get -y update
apt-get -y upgrade
apt-get install -y $missing
bloom-generate rosdebian --os-name ubuntu --os-version xenial --ros-distro kinetic
fakeroot debian/rules binary
cd ..
deb_pack=`find . -maxdepth 1 -name '*.deb'`
pack=${deb_pack#??}
echo "pack: $pack"
mv -f $pack /home/package/