#!/usr/bin/python

# This file is the actual buildtest that is run

from __future__ import print_function
import sys, os, subprocess, shutil

GTESTPASS = '[       OK ]'
GTESTFAIL = '[  FAILED  ]'
PNOSEFAIL = 'FAIL: '
PNOSECONFIGFAIL = 'FAILED ('
PNOSEEXCEPTION = 'Traceback ('
ROSTESTPASS = ' * TESTS: '
ROSTESTFAIL = ' * FAILURES: '
ROSTESTERROR = ' * ERRORS: '


## @brief Run the build and test for a repository of catkin packages
## @param workspace Directory to do work in (typically bind-mounted,
##        code needs to be already checked out to workspace/src/*) /tmp/ii..source
## @param rosdistro Name of the distro to build for, for instance, 'groovy
def run_build_and_test(workspace, rosdistro):
    # need to install dependencies, hack python path, import stuff
    call(['apt-get', 'update'])
    call(['ls', '/home/package'])
    apt_get_install(['python-rosdistro', 'python-catkin-pkg'])  # already there
    if not os.path.abspath("/usr/lib/pymodules/python2.7") in sys.path:
        sys.path.append("/usr/lib/pymodules/python2.7")
    from rosdistro import get_index, get_index_url, get_source_file
    from catkin_pkg import packages

    # Find packages to build
    call(['mkdir', '-p', workspace + '/src/'])
    call(['cp', '-r', '/tmp/build/src', workspace])
    print('Searching for something yummy to build...')
    pkgs = packages.find_packages(workspace + '/src')
    building = [p.name for p in pkgs.values()]
    if len(pkgs) > 0:
        print('  Found packages: %s' % ', '.join(building))
    else:
        raise BuildException('No packages to build or test.')

    # Get build + test dependencies
    print('Examining build dependencies.')
    build_depends = []
    for pkg in pkgs.values():
        for d in pkg.build_depends + pkg.buildtool_depends + pkg.test_depends:
            if not d.name in build_depends and not d.name in building:
                build_depends.append(d.name)
    print('Installing: %s' % ', '.join(build_depends))
    rosdep = RosDepResolver(rosdistro)
    apt_get_install(rosdep.to_aptlist(build_depends))
    pip_install(rosdep.to_piplist(build_depends))

    call(['cp', '-r', '/tmp/build/src', workspace])

    # Get environment
    ros_env = get_ros_env('/opt/ros/%s/setup.bash' % rosdistro)

    os.makedirs(workspace + '/build')
    if os.path.exists(workspace + '/test'):
        shutil.rmtree(workspace + '/test')
    os.makedirs(workspace + '/test')
    os.chdir(workspace + '/build')


    print('catkin_init_workspace')
    if find('CMakeLists.txt','../src') == False:
        call(['catkin_init_workspace', '../src'], ros_env)
    # Workaround for nosetest 1.3.1 issue with non-absolute paths on Trusty
    #  (https://github.com/nose-devs/nose/issues/779)
    test_dir = os.path.realpath('../test')
    call(['cmake', '../src', '-DCATKIN_TEST_RESULTS_DIR=' + test_dir], ros_env)

    print('make')
    call(['make'], ros_env)
    print('make tests')
    call(['make', 'tests'], ros_env)

    # now install the run depends
    print('Examining run dependencies.')
    run_depends = []
    for pkg in pkgs.values():
        for d in pkg.run_depends:
            if not d.name in run_depends and not d.name in building:
                run_depends.append(d.name)
    print('Installing: %s' % ', '.join(run_depends))
    apt_get_install(rosdep.to_aptlist(run_depends))
    pip_install(rosdep.to_piplist(run_depends))

    # Run the tests
    print('make run_tests')
    ros_env = get_ros_env('./devel/setup.bash')
    test_results = call(['make', 'run_tests'], ros_env, return_output=True)

    # Output test results to a file
    f = open(workspace + '/testresults', 'w')

    # Metrics from tests
    gtest_pass = list()
    gtest_fail = list()
    pnose_fail = list()
    pnose_total = 0  # can only count these?
    rostest_pass = 0
    rostest_fail = 0
    rostest_err = 0

    for line in test_results.split('\n'):
        # Is this a gtest pass?
        if line.find(GTESTPASS) > -1:
            name = line[line.find(GTESTPASS) + len(GTESTPASS) + 1:].split(' ')[0]
            gtest_pass.append(name)
        # How about a gtest fail?
        if line.find(GTESTFAIL) > -1:
            name = line[line.find(GTESTFAIL) + len(GTESTPASS) + 1:].split(' ')[0]
            gtest_fail.append(name)
        # pnose fail?
        if line.find(PNOSEFAIL) > -1:
            name = line.split(' ')[2].rstrip()
            pnose_fail.append(name)
        # pnose failed to configure? (issue #17)
        if line.find(PNOSECONFIGFAIL) > -1:
            pnose_fail.append('python configure')
        # pnose exception?
        if line.find(PNOSEEXCEPTION) > -1:
            pnose_fail.append('python exception')
        # is this our total for python?
        if line.find('Ran ') > -1:
            pnose_total += int(line.split(' ')[1])
        # Is this a rostest pass?
        if line.find(ROSTESTPASS) > -1:
            rostest_pass += int(line[line.find(ROSTESTPASS) + len(ROSTESTPASS):].split(' ')[0])
        # Is this a rostest fail?
        if line.find(ROSTESTFAIL) > -1:
            l = line[line.find(ROSTESTFAIL) + len(ROSTESTFAIL):]
            while len(l) > 0:
                try:
                    rostest_fail += int(l.split(' ')[0])
                    break
                except ValueError:
                    # Might have formatting attached, remove 1 character at time
                    l = l[0:-1]
        # Is this a rostest error?
        if line.find(ROSTESTERROR) > -1:
            l = line[line.find(ROSTESTERROR) + len(ROSTESTERROR):]
            while len(l) > 0:
                try:
                    rostest_err += int(l.split(' ')[0])
                    break
                except ValueError:
                    # Might have formatting attached, remove 1 character at time
                    l = l[0:-1]

    # determine if we failed
    passed = len(gtest_pass) + pnose_total - len(pnose_fail) + rostest_pass
    failed = len(gtest_fail) + len(pnose_fail) + rostest_fail + rostest_err
    if failed > 0:
        f.write('*' * 70 + '\n')
        f.write('Failed ' + str(failed) + ' of ' + str(passed + failed) + ' tests.\n')
        for test in gtest_fail + pnose_fail:
            f.write('  failed: ' + test + '\n')
        f.write('See details below\n')
        f.write('*' * 70 + '\n')
    else:
        f.write('Passed ' + str(passed) + ' tests.\n')

    f.write('\n')
    f.write(test_results)
    f.close()

    # Hack so the buildbot can delete this later
    call(['chmod', '777', workspace + '/testresults'])
    cleanup()


## @brief Call a command
## @param command Should be a list
def call(command, envir=None, verbose=True, return_output=False):
    print('Executing command "%s"' % ' '.join(command))
    helper = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True, env=envir)
    if return_output:
        res = ''
    while True:
        output = helper.stdout.readline().decode('utf8', 'replace')
        if helper.returncode is not None or not output:
            break
        if verbose:
            try:
                sys.stdout.write(output)
            except UnicodeEncodeError:
                output = "lost some output, unable to encode in utf-8"
                sys.stdout.write(output)
        if return_output:
            res += output

    helper.wait()
    if helper.returncode != 0:
        msg = 'Failed to execute command "%s" with return code %d' % (command, helper.returncode)
        print('/!\  %s' % msg)
        raise BuildException(msg)
    if return_output:
        return res


## @brief imported from jenkins-scripts/common.py
def get_ros_env(setup_file):
    res = os.environ
    print('Retrieve the ROS build environment by sourcing %s' % setup_file)
    command = ['bash', '-c', 'source %s && env' % setup_file]
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    for line in proc.stdout:
        (key, _, value) = line.partition("=")
        res[key] = value.split('\n')[0]
    proc.communicate()
    if proc.returncode != 0:
        msg = 'Failed to source %s' % setup_file
        print('/!\  %s' % msg)
        raise BuildException(msg)
    return res


## @brief modified version of function found in jenkins-scripts/common.py
def apt_get_install(pkgs, sudo=False):
    cmd = ['apt-get', 'install', '--yes', '--allow-unauthenticated']
    if sudo:
        cmd = ['sudo', ] + cmd

    if len(pkgs) > 0:
        print('calling ' + ' '.join(cmd + pkgs))
        call(cmd + pkgs)
    else:
        print('Not installing anything from apt right now.')


## @brief install pip dependencies
def pip_install(pkgs, sudo=False):
    # Make sure we have pip
    apt_get_install(['python-pip'], sudo=sudo)
    cmd = ["pip", "install"]
    if sudo:
        cmd = ["sudo", ] + cmd
    if len(pkgs) > 0:
        print("Calling " + " ".join(cmd + pkgs))
        call(cmd + pkgs)
    else:
        print('Not installing anything from pip right now.')

def find(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return True
        else:
            return False

## @brief from jenkins-scripts/rosdep.py
class RosDepResolver:
    def __init__(self, rosdistro):
        self.r2a = {}
        self.env = os.environ
        self.env['ROS_DISTRO'] = rosdistro

        # Initialize rosdep database
        print('Ininitalize rosdep database')
        call(['apt-get', 'install', '--yes', 'lsb-release', 'python-rosdep'])
        try:
            call(['rosdep', 'init'], self.env)
        except:
            print('Rosdep is already initialized')
        call(['rosdep', 'update'], self.env)

        print('Building dictionarys from a rosdep db')
        raw_db = call(['rosdep', 'db'], self.env, verbose=False, return_output=True).split('\n')

        for entry in raw_db:
            split_entry = entry.split(' -> ')
            if len(split_entry) < 2:
                continue
            ros_entry = split_entry[0]
            apt_entries = split_entry[1].split(' ')
            self.r2a[ros_entry] = apt_entries

    def to_apt(self, ros_entry):
        if ros_entry not in self.r2a:
            print('Could not find %s in keys.' % ros_entry)
            # horrible hack, that assumes missing deps are actually unlisted, private catkin packages
            return ['ros-' + self.env['ROS_DISTRO'] + '-' + ros_entry.replace('_', '-'), ]
        return self.r2a[ros_entry]

    def to_aptlist(self, ros_entries):
        res = []
        for r in ros_entries:
            if r.endswith("-pip"):
                continue
            for a in self.to_apt(r):
                if not a in res:
                    res.append(a)
        return res

    def to_piplist(self, ros_entries):
        res = []
        for r in ros_entries:
            if r.endswith("-pip"):
                for a in self.r2a[r]:
                    if not a in res:
                        res.append(a)
        return res


class BuildException(Exception):
    def __init__(self, msg):
        cleanup()
        self.msg = msg

    def __str__(self):
        return 'BuildException: %s' % self.msg


## @brief Do some cleanup
def cleanup():
    try:
        if os.path.exists(workspace + '/build'):
            shutil.rmtree(workspace + '/build')
        if os.path.exists(workspace + '/test'):
            shutil.rmtree(workspace + '/test')
        if os.path.exists(workspace + '/src'):
            shutil.rmtree(workspace + '/src')
    except:
        # Workspace variable probably didn't exist; do nothing
        pass


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('')
        print('Usage: testbuild_docker.py <workspace> <rosdistro>')
        print('')
        exit(-1)
    workspace = sys.argv[1]  # for cleanup
    try:
        run_build_and_test(sys.argv[1], sys.argv[2])
    except Exception as e:
        cleanup()
        raise BuildException(str(e))
