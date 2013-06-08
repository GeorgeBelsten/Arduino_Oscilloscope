from threading import Thread
import time
import serial
        
class ArduinoData(object):
    """Creates two threads; first thread continuously reads data from
    the Arduino board, the second thread processes the latest data
    value as quickly as possible, limited by single-threaded CPU
    performance. Data is held in a buffer until read by the visualiser."""
    def __init__(self, init=50):
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
        self.y_buffer = []
        self.last_received = ''
        # Start data collection and data processing threads
        Thread(target=self.data_collector, args=(self.port,)).start()
        Thread(target=self.data_processor, args=()).start()
    
    def data_collector(self, port):
        """Loops continuously, outputting the last received data
        value from the Arduino board as self.last_received."""
        data_buffer = ''
        while True:
            data_buffer = data_buffer + port.read()
            if '\n' in data_buffer:
                # Guaranteed to produce at least two lines of data
                lines = data_buffer.split('\n')
                # Output second to last line, return last line to buffer
                self.last_received = lines[-2]
                data_buffer = lines[-1]
            
    def data_processor(self):
        """Processes the data from the collector thread as quickly
        as possible; appends processed data to a buffer."""
        while True:
            try:
                # Float latest data value and add to buffer
                self.y_buffer.append(float(self.last_received))
            except ValueError:
                print "Data processor exception!"
                self.y_buffer.append(2.5)
                time.sleep(0.01)
        
    def print_data(self):
        """Prints the length of the data buffer."""
        print "Data length: ",len(self.y_buffer)
            
    def get_data(self):
        """Returns the data buffer."""
        return self.y_buffer
        
    def clear_buffer(self):
        """Clears the data buffer."""
        self.y_buffer = []
            
if __name__=='__main__':
    data = ArduinoData()
    # Print data buffer length every second, for troubleshooting
    while True:
        time.sleep(1)
        data.print_data()
        data.clear_buffer()