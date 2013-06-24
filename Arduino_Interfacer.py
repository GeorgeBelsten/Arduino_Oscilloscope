"""
Continuously reads data from the Arduino board and processes it.
Running this file directly prints the length of the data queue each
second, for troubleshooting purposes. This file must be in the same
directory as Arduino_Visualiser.py to run the visualiser.
"""

from multiprocessing import Process, Queue
import time
import serial
        
class ArduinoData(object):
    def __init__(self, init=50):
        # Create queues to hold the raw and processed data
        self.raw_data = Queue()
        self.processed_data = Queue()
        # Start separate processes for data collection and processing
        Process(target=self.data_collector, args=()).start()
        Process(target=self.data_processor, args=()).start()
    
    def data_collector(self):
        """Continuously reads data from the serial port, and adds it
        to the raw data queue."""
        # Continuously search for Arduino board,
        # initialise serial connection when found
        self.port = 0
        print "Searching for Arduino..."
        while self.port is 0:
            try:
                self.port = serial.Serial(
                    port = 'COM3',
                    baudrate = 115200,
                    timeout = 0.1
                    )
            except serial.serialutil.SerialException:
                time.sleep(0.01)     
        print "Arduino found! Waiting for Arduino to start..."
        # Wait two seconds for Arduino to start producing proper data
        time.sleep(2)
        print "Starting data collection..."
        data_buffer = ''
        while True:
            data_buffer = data_buffer + self.port.read()
            if '\n' in data_buffer or '\r' in data_buffer:
                lines = data_buffer.split('\n')
                data_buffer = ''
                for line in lines:
                    self.raw_data.put(line)
            
    def data_processor(self):
        """Processes data from the raw data queue, and adds it to the
        processed data queue."""
        while True:
            raw_dlist = []
            while not self.raw_data.empty():
                raw_dlist.append(self.raw_data.get())
            for d in raw_dlist:
                try:
                    if len(d) == 5:
                        y = float(d)
                        self.processed_data.put(y)
                except ValueError:
                    pass
        
    def print_data(self):
        """Prints the length of the data buffer."""
        print "Data length: ",self.processed_data.qsize()
            
    def get_data(self):
        """Returns the processed data queue."""
        data_return = []
        while not self.processed_data.empty():
            data_return.append(self.processed_data.get())
        return data_return
        
            
if __name__=='__main__':
    data = ArduinoData()
    # Print data buffer length every second, for troubleshooting
    while True:
        time.sleep(1)
        data.print_data()
    time.sleep(20)