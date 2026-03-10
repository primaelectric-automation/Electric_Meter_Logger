import logging
import argparse
import time
import csv  # Added for CSV support
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from pymodbus.client import ModbusSerialClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.ERROR)

class ModbusPlotter:
    def __init__(self, port, filename="power_log.csv"):
        self.client = ModbusClient(port=port, baudrate=9600, parity='N', stopbits=1, bytesize=8, timeout=1)
        if not self.client.connect():
            raise ConnectionError(f"Could not connect to {port}")

        # CSV Initialization
        self.filename = filename
        self.init_csv()

        self.limit = 60 
        self.xdata = []
        self.ydata = {'v': [[],[],[]], 'i': [[],[],[]], 'p': [[],[],[]]}
        
        self.fig, (self.ax_v, self.ax_i, self.ax_p) = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
        self.lines_v = [self.ax_v.plot([], [], label=f'Ph{i+1}')[0] for i in range(3)]
        self.lines_i = [self.ax_i.plot([], [], label=f'Ph{i+1}')[0] for i in range(3)]
        self.lines_p = [self.ax_p.plot([], [], label=f'Ph{i+1}')[0] for i in range(3)]

        for ax, lbl in zip([self.ax_v, self.ax_i, self.ax_p], ['Volts', 'Amps', 'kW']):
            ax.set_ylabel(lbl)
            ax.legend(loc='upper right', ncol=3)

    def init_csv(self):
        """Creates the CSV and writes the header."""
        with open(self.filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'V1', 'V2', 'V3', 'I1', 'I2', 'I3', 'P1', 'P2', 'P3'])

    def log_to_csv(self, v, i, p):
        """Appends a new row of data to the CSV."""
        with open(self.filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            # Combine timestamp with all phase values
            writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S")] + v + i + p)

    def update(self, frame):
        rv = self.client.read_holding_registers(66, 6, slave=1)
        ri = self.client.read_holding_registers(88, 6, slave=1)
        rp = self.client.read_holding_registers(100, 6, slave=1)

        if not any(r.isError() for r in [rv, ri, rp]):
            dv = BinaryPayloadDecoder.fromRegisters(rv.registers, Endian.BIG, Endian.BIG)
            di = BinaryPayloadDecoder.fromRegisters(ri.registers, Endian.BIG, Endian.BIG)
            dp = BinaryPayloadDecoder.fromRegisters(rp.registers, Endian.BIG, Endian.BIG)

            v = [dv.decode_32bit_uint() / 10000 for _ in range(3)]
            i = [di.decode_32bit_uint() / 10000 for _ in range(3)]
            p = [dp.decode_32bit_uint() / 10000 for _ in range(3)]

            # Log to CSV
            self.log_to_csv(v, i, p)

            self.xdata.append(time.time())
            if len(self.xdata) > self.limit: self.xdata.pop(0)

            for j in range(3):
                # Fixed a minor logic bug from original: 
                # j loop should update specific phase lists correctly
                self.ydata['v'][j].append(v[j])
                self.ydata['i'][j].append(i[j])
                self.ydata['p'][j].append(p[j])
                
                if len(self.ydata['v'][j]) > self.limit: self.ydata['v'][j].pop(0)
                if len(self.ydata['i'][j]) > self.limit: self.ydata['i'][j].pop(0)
                if len(self.ydata['p'][j]) > self.limit: self.ydata['p'][j].pop(0)

            for idx in range(3):
                self.lines_v[idx].set_data(range(len(self.xdata)), self.ydata['v'][idx])
                self.lines_i[idx].set_data(range(len(self.xdata)), self.ydata['i'][idx])
                self.lines_p[idx].set_data(range(len(self.xdata)), self.ydata['p'][idx])

            for ax in [self.ax_v, self.ax_i, self.ax_p]:
                ax.relim()
                ax.autoscale_view()
            
            print(f"\rV: {v[0]:.1f} {v[1]:.1f} {v[2]:.1f} | I: {i[0]:.2f} {i[1]:.2f} {i[2]:.2f}", end="")
            
        return self.lines_v + self.lines_i + self.lines_p

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default='COM4')
    parser.add_argument('--output', default='power_log.csv', help='CSV filename')
    args = parser.parse_args()

    monitor = ModbusPlotter(args.port, args.output)
    ani = FuncAnimation(monitor.fig, monitor.update, interval=1000, cache_frame_data=False)
    plt.tight_layout()
    plt.show()
    monitor.client.close()