"""Constants for the duco integration."""

DOMAIN = "duco"
MODBUS_DOMAIN = "modbus"
CONF_HUB = "hub"
CONF_FAKE = "fake"
MODEL_NAME = "DucoBox Focus"
MODBUS_CONFIG_EXAMPLE = """
            modbus:
              - name: "duco_hub"
                close_comm_on_error: true
                delay: 2
                timeout: 5
                type: serial
                baudrate: 9600
                bytesize: 8
                method: rtu
                parity: N
                port: /dev/ttyUSB0
                stopbits: 1
"""
