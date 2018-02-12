#!/bin/sh

set -x

if [ $# -eq 1 ]
        then
        newUUID="$(echo $( nova show $1 | grep -w "id" | awk -F '|' '{print $3} ' ) )"
        alarmID="$(echo "$( ceilometer alarm-list | grep -w "rtOpenstack_$newUUID" | awk -F '|' '{print $2} ')")"
        
        ceilometer alarm-delete $alarmID
        nova delete $newUUID
else    
        echo "Usage:  ./startVM.sh NAME FLAVOR IMAGE WCET PERIOD"
        echo "    WCET/Period format: (WCET1,WCET2) (PERIOD1,PERIOD2)"
        echo "    Example: Tasks 20/100 and 40/200"
        echo "        startVM.sh testVM m1.medium cirros-0.3.4-x86_64 \"(20,40)\" \"(100,200)\""
        
fi
