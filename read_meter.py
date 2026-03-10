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
log.setLevel(logging.ERROR) # Set to ERROR to keep the console clean

def run_monitor(port_name):
    # Initialize the Modbus RTU Client
    client = ModbusClient(
        port=port_name,
        baudrate=9600,
        parity='N',
        stopbits=1,
        bytesize=8,
        timeout=1
    )

    print(f"Connecting to {port_name}...")
    if not client.connect():
        print(f"Failed to connect to {port_name}. Check your connections.")
        return

    try:
        print("Starting monitoring. Press Ctrl+C to stop.\n")
        while True:
            # Reading 6 registers starting at 66
            result = client.read_holding_registers(address=66, count=6, slave=1)

            if not result.isError():
                decoder = BinaryPayloadDecoder.fromRegisters(
                    result.registers, 
                    byteorder=Endian.BIG, 
                    wordorder=Endian.BIG
                )

                # Decode the values
                val_P1 = decoder.decode_32bit_uint() / 10000
                val_P2 = decoder.decode_32bit_uint() / 10000
                val_P3 = decoder.decode_32bit_uint() / 10000
                
                # Clear line and print (using \r to keep it on one line if preferred)
                print(f"L1: {val_P1:>7.2f} V | L2: {val_P2:>7.2f} V | L3: {val_P3:>7.2f} V", end='\r')
            else:
                print(f"\nModbus Error: {result}")

            time.sleep(1) # Wait for 1 second

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    except ModbusException as e:
        print(f"\nCommunication Error: {e}")
    finally:
        client.close()
        print("Connection closed.")

if __name__ == "__main__":
    # --- Parser Setup ---
    parser = argparse.ArgumentParser(description="Modbus RTU Voltage Monitor")
    parser.add_argument(
        '--port', 
        type=str, 
        default='COM4', 
        help='The serial port to use (e.g., COM4 or /dev/ttyUSB0)'
    )
    
    args = parser.parse_args()
    
    # Run the function with the parsed port
    run_monitor(args.port)