#!/bin/sh

if [ "$#" -eq 0 ]; then
    exec ./main
elif [ "$1" = "--sync" ]; then
    exec ./main --sync
else
    echo "Usage: $0 [--sync]"
    echo "  기본 실행 : Docker 컨테이너 정보를 Notion에 추가"
    echo "  --sync  : 기존 데이터를 덮어쓰며 Notion과 동기화"
    exit 1
fi
