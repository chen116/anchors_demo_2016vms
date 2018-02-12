#!/bin/sh

service mongodb stop
rm -f /var/lib/mongodb/ceilometer*
rm -r /var/lib/mongodb/journal/prealloc.*
service mongodb start
sleep 3

mongo --host controller --eval '
  db = db.getSiblingDB("ceilometer");
  db.addUser({user: "ceilometer",
  pwd: "anch0rs",
  roles: [ "readWrite", "dbAdmin" ]})'

service ceilometer-agent-central restart
service ceilometer-agent-notification restart
service ceilometer-api restart
service ceilometer-collector restart
service ceilometer-alarm-evaluator restart
service ceilometer-alarm-notifier restart
service ceilometer-agent-compute restart
