from threading import Thread
from multiprocessing import Process, Queue, Value
import time
import serial
import types
        
class ArduinoData(object):
    """Creates two threads; first thread continuously reads data from
    the Arduino board, the second thread processes the latest data
    value approximately 1000 times a second. Data is held in a buffer
    until read by the visualiser."""
    def __init__(self, init=50):
        # Continuously search for Arduino board,
        # initialise serial connection when found
        self.port = 0
        print "Searching for Arduino..."
        while self.port is 0:
            try:
                self.port = serial.Serial(
                    port = 'COM4',
                    baudrate = 115200,
                    timeout = 0.1
                    )
            except serial.serialutil.SerialException:
                time.sleep(0.01)     
        print "Arduino found! Waiting for Arduino to start..."
        # Wait two seconds for Arduino to start producing proper data
        time.sleep(2)
        
        print "Starting data collection..."
        self.raw_data = Queue()
        self.processed_data = Queue()
        
        Thread(target=self.data_collector, args=()).start()
        Process(target=self.data_processor, args=()).start()
    
    def data_collector(self):
        data_buffer = ''
        while True:
            data_buffer = data_buffer + self.port.read()
            if '\n' in data_buffer or '\r' in data_buffer:
                lines = data_buffer.split('\n')
                data_buffer = ''
                self.raw_data.put(lines[-1])
            
    def data_processor(self):
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
        """Returns the data buffer."""
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