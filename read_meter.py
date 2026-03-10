import logging
from pymodbus.client import ModbusSerialClient as ModbusClient
from pymodbus.exceptions import ModbusException
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

# Configure logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

def read_fort_sensor():
    # Initialize the Modbus RTU Client for Windows
    client = ModbusClient(
        port='COM4',        # Changed from /dev/ttyUSB0 to COM4
        baudrate=9600,      
        parity='N',
        stopbits=1,
        bytesize=8,
        timeout=1
    )

    # Connect to the device
    if not client.connect():
        print("Failed to connect to COM4. Check if the device is plugged in or the port is used by another app.")
        return

    try:
        # Reading registers
        result = client.read_holding_registers(address=66, count=2, slave=1)

        if not result.isError():
            # Decoding the payload
            # Note: For pymodbus 3.x, ensure you use the correct Endian constants
            decoder = BinaryPayloadDecoder.fromRegisters(
                result.registers, 
                byteorder=Endian.BIG, 
                wordorder=Endian.BIG
            )

            decoded_value = decoder.decode_32bit_uint()
            print(f"32-bit Unsigned Value from COM4: {decoded_value}")
        else:
            print(f"Modbus Error: {result}")

    except ModbusException as e:
        print(f"Communication Error: {e}")
    
    finally:
        client.close()

if __name__ == "__main__":
    read_fort_sensor()