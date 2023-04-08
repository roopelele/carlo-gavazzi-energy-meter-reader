#!/bin/bash

function check_file() {
    if [ ! -f "$1" ]; then
        echo 0 > "$1"
    fi
}

check_file /dev/shm/P.txt
check_file /dev/shm/A_0.txt
check_file /dev/shm/A_1.txt
check_file /dev/shm/A_2.txt
