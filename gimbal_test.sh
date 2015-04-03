#!/bin/bash

MIN_GIMBAL=900
MAX_GIMBAL=2100

while getopts ":s" opt; do
    case $opt in
        s)
            echo 204 > /sys/class/soft_pwm/export
            echo 20000 > /sys/class/soft_pwm/pwm204/period

            echo 200 > /sys/class/soft_pwm/export
            echo 20000 > /sys/class/soft_pwm/pwm200/period
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

let GIMBAL_RANGE=$MAX_GIMBAL-$MIN_GIMBAL
function normalize() {
    let GIMBAL_VAL=$1*GIMBAL_RANGE
    let FINAL=($GIMBAL_VAL/100)+MIN_GIMBAL
    echo $FINAL > /sys/class/soft_pwm/pwm$2/pulse
}

while true; do
    read test1 test2
    normalize $test1 204
    normalize $test2 200
done

