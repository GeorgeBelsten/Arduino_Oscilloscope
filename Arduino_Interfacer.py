from threading import Thread
import time
import serial
        
class ArduinoData(object):
    def __init__(self, init=50):
        self.port = 0
        self.last_received = ''
        self.y_buffer = []
        print "Searching for Arduino..."
        while self.port is 0:
            try:
                self.port = port = serial.Serial(
                    port = 'COM3',
                    baudrate = 115200,
                    timeout = 0.1
                    )
            except serial.serialutil.SerialException:
                time.sleep(0.01)
            
        print "Arduino found! Waiting for Arduino to start..."
        time.sleep(2)
        print "Starting data collection..."
        Thread(target=self.data_collector, args=(self.port,)).start()
        Thread(target=self.data_processor, args=()).start()
    
    def data_collector(self, port):
        data_buffer = ''
        while True:
            data_buffer = data_buffer + port.read(port.inWaiting())
            if '\n' in data_buffer:
                lines = data_buffer.split('\n')
                self.last_received = lines[-2]
                data_buffer = lines[-1]
            
    def data_processor(self):
        while True:
            try:
                self.y_buffer.append(float(self.last_received))
            except ValueError:
                print "Data processor exception!"
            time.sleep(0.001)
        
    def print_data(self):
        print self.y_buffer
            
    def get_data(self):
        return self.y_buffer
        
    def clear_buffer(self):
        self.y_buffer = []
            
if __name__=='__main__':
    data = ArduinoData()
    while True:
        time.sleep(1)
        data.print_data()
        data.clear_buffer()