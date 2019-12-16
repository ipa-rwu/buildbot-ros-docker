#!/bin/bash
cd /home/package
echo "build package: $package"
shortname=${package%?}
short_name=`tr '-' '_' <<<"$shortname"`
python /home/rosdep/update_private_rosdep.py /home/package/private.yaml $short_name $shortname
deb_pack=`find . -name $package`
deb_pack=${deb_pack#??}
IFS='_' read -r -a strarr <<< "$deb_pack"
pack=${strarr}
add_version=${strarr[1]}
echo "new version: $add_version"
existline=`reprepro -b /var/www/building/ubuntu/ list xenial $pack`
IFS=' ' read -r -a strarr <<< "$existline"
exist_version=${strarr[2]}
echo "old version: $exist_version"
if [ ! -z "$existline" ];
then
	echo "old: $exist_version"
	echo "new: $add_version"
	if [ "$add_version" == "$exist_version" ];
	then
		echo "exist"
	else
		reprepro.exp /var/www/building/ubuntu/ includedeb xenial $deb_pack
	fi
else
	reprepro.exp /var/www/building/ubuntu/ includedeb xenial $deb_pack
fi
rm $deb_pack