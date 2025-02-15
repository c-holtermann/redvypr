import datetime
import logging
import queue
from PyQt5 import QtWidgets, QtCore, QtGui
import time
import numpy as np
import serial
import serial.tools.list_ports
import logging
import sys


description = 'Reading data from a serial device'

logging.basicConfig(stream=sys.stderr)
logger = logging.getLogger('serial_device')
logger.setLevel(logging.DEBUG)


def start(dataqueue,comqueue,serial_name,baud,max_size=10000,dt = 0.05):
    """
    dt: time.sleep(dt) parameter
    """
    funcname = __name__ + '.start()'
    chunksize = 1000 # The maximum amount of bytes read with one chunk
    logger.debug(funcname + ':Starting reading serial data')        
    nmea_sentence = ''
    sentences = 0
    bytes_read = 0
    ttest = time.time()
    serial_device = False
    if True:
        try:
            serial_device = serial.Serial(serial_name,baud,timeout=0.05)
            #print('Serial device 0',serial_device)            
            #serial_device.timeout(0.05)
            #print('Serial device 1',serial_device)                        
        except Exception as e:
            #print('Serial device 2',serial_device)
            logger.debug(funcname + ': Exception open_serial_device {:s} {:d}: '.format(serial_name,baud) + str(e))
            return False

    got_dollar = False    
    while True:
        try:
            com = comqueue.get(block=False)
            logger.debug('received' + str(com))
            break
        except:
            pass


        time.sleep(dt)
        ndata = serial_device.inWaiting()
        if(ndata < 100):
            ndata = 100
            
        rawdata_all = serial_device.read(ndata)
        if((time.time() - ttest)>10):
            print('ndata',len(rawdata_all),'rawdata',rawdata_all,type(rawdata_all))
            ttest = time.time()
            
        for rawdata in rawdata_all:
            try:
                value = chr(rawdata) # .decode('utf-8')
                #print('data',rawdata,value)
                bytes_read += 1
                nmea_sentence += value
                if(len(nmea_sentence) > max_size):
                    nmea_sentence = ''
                    
                if(value == '$'):
                    got_dollar = True
                    nmea_sentence = value
                    # Get the time
                    ti = time.time()

                elif((value == '\n') and (got_dollar)):
                    got_dollar = False                    
                    data = {'t':time.time()}
                    data['nmeatime'] = ti
                    data['serialdevice'] = serial_device.name
                    data['nmea'] = nmea_sentence
                    data['bytes_read'] = bytes_read
                    data['nmea_sentences_read'] = sentences
                    logger.debug(funcname + ':Read sentence:' + nmea_sentence)
                    nmea_sentence = ''
                    sentences += 1
                    try:
                        dataqueue.put(data)
                    except Exception as e:
                        logger.debug(funcname + ': Dataqueue put exception')

            except Exception as e:
                logger.debug(':Exception:' + str(e))            

class Device():
    def __init__(self,dataqueue=None,comqueue=None,datainqueue=None):
        """
        """
        self.publish     = True # publishes data, a typical device is doing this
        self.subscribe   = False  # subscribing data, a typical datalogger is doing this
        self.datainqueue = datainqueue
        self.dataqueue   = dataqueue        
        self.comqueue    = comqueue
        self.serial_device = None
        self.serial_name = ''
        self.baud = 0
        self.sentences = 0
        
        
        
    def thread_status(self,status):
        """ Function that is called by redvypr, allowing to update the status of the device according to the thread 
        """
        self.threadalive = status['threadalive']
        pass

    def start(self):
        funcname = __name__ + '.start()'                                
        logger.debug(funcname)
        start(self.dataqueue,self.comqueue,self.serial_name,self.baud)
        

    def __str__(self):
        sstr = 'serial device'
        return sstr



class initDeviceWidget(QtWidgets.QWidget):
    device_start = QtCore.pyqtSignal(Device)
    device_stop = QtCore.pyqtSignal(Device)        
    def __init__(self,device=None):
        super(QtWidgets.QWidget, self).__init__()
        layout        = QtWidgets.QVBoxLayout(self)
        self.device   = device
        self.serialwidget = QtWidgets.QWidget()
        self.init_serialwidget()
        self.label    = QtWidgets.QLabel("Serial device device")
        #self.startbtn = QtWidgets.QPushButton("Open device")
        #self.startbtn.clicked.connect(self.start_clicked)
        #self.stopbtn = QtWidgets.QPushButton("Close device")
        #self.stopbtn.clicked.connect(self.stop_clicked)
        layout.addWidget(self.label)        
        layout.addWidget(self.serialwidget)
        #layout.addWidget(self.startbtn)
        #layout.addWidget(self.stopbtn)
        
    def thread_status(self,status):
        self.update_buttons(status['threadalive'])

    def init_serialwidget(self):
        """Fills the serial widget with content
        """
        layout = QtWidgets.QGridLayout(self.serialwidget)
        # Serial baud rates
        baud = [300,600,1200,2400,4800,9600,19200,38400,57600,115200,576000,921600]
        self._combo_serial_devices = QtWidgets.QComboBox()
        #self._combo_serial_devices.currentIndexChanged.connect(self._serial_device_changed)
        self._combo_serial_baud = QtWidgets.QComboBox()
        for b in baud:
            self._combo_serial_baud.addItem(str(b))

        self._combo_serial_baud.setCurrentIndex(4)
        self._button_serial_openclose = QtWidgets.QPushButton('Open')
        self._button_serial_openclose.clicked.connect(self.start_clicked)


        # Check for serial devices and list them
        for comport in serial.tools.list_ports.comports():
            self._combo_serial_devices.addItem(str(comport.device))

        #How to differentiate packets
        self._packet_ident_lab = QtWidgets.QLabel('Packet identification')
        self._packet_ident     = QtWidgets.QComboBox()
        self._packet_ident.addItem('NMEA')
        self._packet_ident.addItem('newline \\n')
        self._packet_ident.addItem('newline \\r\\n')
        self._packet_ident.addItem('None')
        # Max packetsize
        self._packet_size_lab   = QtWidgets.QLabel("Maximum packet size")
        self._packet_size_lab.setToolTip('The number of received bytes after which a packet is sent.\n Add 0 for no size check')
        onlyInt = QtGui.QIntValidator()
        self._packet_size       = QtWidgets.QLineEdit()
        self._packet_size.setValidator(onlyInt)
        self._packet_size.setText('0')
        #self.packet_ident

        layout.addWidget(self._packet_ident,0,1)
        layout.addWidget(self._packet_ident_lab,0,0)
        layout.addWidget(self._packet_size_lab,0,2)
        layout.addWidget(self._packet_size,0,3)        
        layout.addWidget(self._combo_serial_devices,1,0)
        layout.addWidget(self._combo_serial_baud,1,1)
        layout.addWidget(self._button_serial_openclose,1,2)
        
    
    def update_buttons(self,thread_status):
        """ Updating all buttons depending on the thread status (if its alive, graying out things)
        """
        if(thread_status):
            self._button_serial_openclose.setText('Close')
            self._combo_serial_baud.setEnabled(False)
            self._combo_serial_devices.setEnabled(False)
        else:
            self._button_serial_openclose.setText('Open')
            self._combo_serial_baud.setEnabled(True)
            self._combo_serial_devices.setEnabled(True)
        
            
    def start_clicked(self):
        #print('Start clicked')
        button = self._button_serial_openclose
        #print('Start clicked:' + button.text())
        if('Open' in button.text()):
            button.setText('Close')
            serial_name = str(self._combo_serial_devices.currentText())
            serial_baud = int(self._combo_serial_baud.currentText())
            self.device.serial_name = serial_name
            self.device.baud = serial_baud
            self.device_start.emit(self.device)
        else:
            self.stop_clicked()

    def stop_clicked(self):
        #print('Stop clicked')
        button = self._button_serial_openclose
        self.device_stop.emit(self.device)
        button.setText('Closing') 
        #self._combo_serial_baud.setEnabled(True)
        #self._combo_serial_devices.setEnabled(True)      



class displayDeviceWidget(QtWidgets.QWidget):
    def __init__(self):
        super(QtWidgets.QWidget, self).__init__()
        layout        = QtWidgets.QVBoxLayout(self)
        hlayout        = QtWidgets.QHBoxLayout()
        self.bytes_read = QtWidgets.QLabel('Bytes read: ')
        self.lines_read = QtWidgets.QLabel('Lines read: ')
        self.text     = QtWidgets.QPlainTextEdit(self)
        self.text.setReadOnly(True)
        self.text.setMaximumBlockCount(10000)
        hlayout.addWidget(self.bytes_read)
        hlayout.addWidget(self.lines_read)
        layout.addLayout(hlayout)
        layout.addWidget(self.text)

    def update(self,data):
        #print('data',data)
        bstr = "Bytes read: {:d}".format(data['bytes_read'])
        lstr = "Lines read: {:d}".format(data['nmea_sentences_read'])
        self.bytes_read.setText(bstr)
        self.lines_read.setText(lstr)
        self.text.insertPlainText(str(data['nmea']))
        
