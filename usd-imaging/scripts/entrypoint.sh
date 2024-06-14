#!/bin/sh

export DISPLAY=:1
xinit -- /usr/bin/Xvfb :1 -screen 0 1024x768x24 >> /opt/xinit-xvfb.log 2>&1 &
sleep 0.1

$@

