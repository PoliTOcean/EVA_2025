#!/bin/bash

gnome-terminal -- bash -c '
JANUS_INSTALL_PREFIX="/opt/janus"
JANUS_CONFIG_DIR="${JANUS_INSTALL_PREFIX}/etc/janus"
/opt/janus/bin/janus -F "${JANUS_CONFIG_DIR}"
exec bash
'

