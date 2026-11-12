#!/bin/bash

cd /home/dronenavcp/api.dronenav.org || exit 1

exec /bin/flock -n /tmp/dronenav-turn-collector.lock \
  /home/dronenavcp/virtualenv/api.dronenav.org/3.11/bin/python \
  -m app.navproxy.telemetry.turn_collector \
  >> /home/dronenavcp/logs/turn_collector.log 2>&1
