import yaml, re
import sys

# rosdep_path /home/package/rosdep_private.yaml
# rospack: ros-kinetic-*
# ros_pack: ros_kinetic_*
def update_rosdep(rosdep_path, ros_pack, rospack):
    i = 0
    patten = "ros_kinetic_"
    pack = re.split(patten, ros_pack)[1]
    print(pack)
    with open(rosdep_path) as f:
        doc = yaml.safe_load(f)
        for key, v in doc.items():
            if re.search(pack+"$", key)!= None :
                i = 1
    if i == 0:
        data = {}
        data[pack] = (
            dict(
                ubuntu=rospack
            )
        )
        with open(rosdep_path,'a') as outfile:
                    yaml.safe_dump(data, outfile)

if __name__=="__main__":
    if len(sys.argv) < 3:
        print('')
        print('Usage: unique_docker_deb.py <composefile> <package>')
        print('')
        exit(-1)
    rosdep_path = sys.argv[1]
    ros_pack = sys.argv[2]
    rospack = sys.argv[3]
    update_rosdep(rosdep_path, ros_pack, rospack)