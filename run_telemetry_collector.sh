#!/bin/bash

cd /home/dronenavcp/api.dronenav.org || exit 1

exec /bin/flock -n /tmp/dronenav-telemetry-collector.lock \
  /home/dronenavcp/virtualenv/api.dronenav.org/3.11/bin/python \
  -m app.navproxy.telemetry.collector \
  >> /home/dronenavcp/logs/telemetry_collector.log 2>&1
