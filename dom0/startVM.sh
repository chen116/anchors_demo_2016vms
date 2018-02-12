#!/bin/sh

set -x

if [ $# -eq 3 ]
        then
        # This is a non-RT VM
        echo "non-RT VM"
        newUUID="$(echo $( nova boot --flavor $2 --image $3 --nic net-id=$( echo $( nova net-list | grep private | awk -F '|' '{print $2}' ) ) $1 | grep -w "id" | awk -F '|' '{print $3} ' ) )"

elif [ $# -eq 5 ]
        then
        # This is a RT VM
        echo "RT VM"
        newUUID="$(echo $( nova boot --flavor $2 --image $3 --nic net-id=$( echo $( nova net-list | grep private | awk -F '|' '{print $2}' ) ) --hint rt_type=rt_csa --hint rt_period="$5" --hint rt_budget="$4" $1 | grep -w "id" | awk -F '|' '{print $3} ' ) )"
        ceilometer alarm-threshold-create --name rtOpenstack_$newUUID --description "This watches for any missed deadlines" --meter-name rtOpenstack_$newUUID --threshold 1 --comparison-operator ge --enabled True --repeat-actions True --evaluation-periods 1 --period 1 --statistic max --alarm-action "http://172.16.91.138:8001"
        until [[ "$(nova show ${newUUID} | awk '/status/ {print $4}')" == "ACTIVE" ]]; do
                :
        done
#        nova meta $1 set taskset="\"$(python myScripts/genTaskMetadata.py $4 $5 $5)\""

else
        echo "Usage:  ./startVM.sh NAME FLAVOR IMAGE WCET PERIOD"
        echo "    WCET/Period format: (WCET1,WCET2) (PERIOD1,PERIOD2)"
        echo "    Example: Tasks 20/100 and 40/200"
        echo "        startVM.sh testVM m1.medium cirros-0.3.4-x86_64 \"(20,40)\" \"(100,200)\""

fi
