import logging
import argparse
import time
from pymodbus.client import ModbusSerialClient as ModbusClient
from pymodbus.exceptions import ModbusException
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

# Configure logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.ERROR)

def run_monitor(port_name):
    client = ModbusClient(
        port=port_name,
        baudrate=9600,
        parity='N',
        stopbits=1,
        bytesize=8,
        timeout=1
    )

    if not client.connect():
        print(f"Failed to connect to {port_name}.")
        return

    try:
        print(f"Monitoring {port_name}. Press Ctrl+C to stop.\n")
        while True:
            # --- BLOCK 1: Voltage (Registers 66, 68, 70) ---
            res_v = client.read_holding_registers(address=66, count=6, slave=1)
            
            # --- BLOCK 2: Current (Registers 88, 90, 92) ---
            res_i = client.read_holding_registers(address=88, count=6, slave=1)

            if not res_v.isError() and not res_i.isError():
                # Decode Voltage
                dec_v = BinaryPayloadDecoder.fromRegisters(res_v.registers, Endian.BIG, Endian.BIG)
                v1, v2, v3 = [dec_v.decode_32bit_uint() / 10000 for _ in range(3)]

                # Decode Current
                dec_i = BinaryPayloadDecoder.fromRegisters(res_i.registers, Endian.BIG, Endian.BIG)
                i1, i2, i3 = [dec_i.decode_32bit_uint() / 10000 for _ in range(3)]
                
                # Combined Print Output
                # \033[K clears the line to prevent ghost characters
                output = (f"VOLTS: {v1:>6.1f}V {v2:>6.1f}V {v3:>6.1f}V | "
                          f"AMPS: {i1:>6.2f}A {i2:>6.2f}A {i3:>6.2f}A")
                print(f"\r\033[K{output}", end='', flush=True)

            else:
                print(f"\nRead Error - V: {res_v} | I: {res_i}")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=str, default='COM4')
    args = parser.parse_args()
    run_monitor(args.port)