#!/bin/bash 
# project name
export COMPOSE_PROJECT_NAME=ros-buildbot-docker
#
export BUILDBOT_WORKER_NAME_1=worker-1
export BUILDBOT_WORKER_PASS_1=1234
export BUILDBOT_WORKER_NAME_2=worker-2
export BUILDBOT_WORKER_PASS_2=1234
export BUILDBOT_WEB_URL=http://localhost:8010/
export BUILDBOT_WEB_PORT=8010
export BUILDBOT_PRIVATE_INDEX=git@github.com:ipa-rwu/rosdistro-scalable.git
export BUILDBOT_WORKER_PORT=9989
export BUILDBOT_ROSINSTALL_INDEX=git@github.com:ipa-rwu/scalable_system_setup.git
export LOCAL_RESPOSITORY=local-repository:80
export SINGING_KEY=8617EB404586F58E
export DEVEL_TIME_H=12
export DEVEL_TIME_M=59
export DEVEL_TIME_H_D=13
export DEVEL_TIME_M_D=30
export DEB_TIME_H=14
export DEB_TIME_M=0
export DOC_TIME_H=2
export DOC_TIME_M=30
