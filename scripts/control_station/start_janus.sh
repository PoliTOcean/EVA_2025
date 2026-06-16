#!/bin/bash

JANUS_INSTALL_PREFIX="/opt/janus"
JANUS_CONFIG_DIR="${JANUS_INSTALL_PREFIX}/etc/janus"

exec "${JANUS_INSTALL_PREFIX}/bin/janus" -F "${JANUS_CONFIG_DIR}"
