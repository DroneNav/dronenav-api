#!/bin/bash

cd /home/dronenavcp/api.dronenav.org || exit 1

exec /bin/flock -n /tmp/dronenav-rse-collector.lock \
  /home/dronenavcp/virtualenv/api.dronenav.org/3.11/bin/python \
  -m app.navproxy.rse.collector \
  >> /home/dronenavcp/logs/rse_collector.log 2>&1
