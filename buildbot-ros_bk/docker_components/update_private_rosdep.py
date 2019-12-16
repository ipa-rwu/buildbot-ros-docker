import yaml, re
import sys

# rosdep_path /home/package/rosdep_pricate.yaml
def update_rosdep(rosdep_path, rospack):
    i = 0
    with open(rosdep_path) as f:
        doc = yaml.safe_load(f)
        for key, v in doc.items():
            if re.search(rospack+"$", key)!= None :
                longname = v['ubuntu']
                i = 1
    if i == 0:
        data = {}
        data[rospack] = (
            dict(
                ubuntu='ros-kinetic-' + rospack
            )
        )
        with open(rosdep_path,'a') as outfile:
                    yaml.safe_dump(data, outfile)

if __name__=="__main__":
    if len(sys.argv) < 2:
        print('')
        print('Usage: update_private_rosdep.py <rosdep_path> <rospack>')
        print('')
        exit(-1)
    rosdep_path = sys.argv[1]
    rospack = sys.argv[2]
    update_rosdep(rosdep_path, rospack)

