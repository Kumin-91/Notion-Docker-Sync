#!/bin/sh

if [ "$1" = "--sync" ]; then
    exec ./notion-docker --sync
else
    exec ./notion-docker
fi