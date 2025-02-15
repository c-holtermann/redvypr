import datetime
import logging
import queue
from PyQt5 import QtWidgets, QtCore, QtGui
import time
import numpy as np
import logging
import sys
import yaml
import copy

logging.basicConfig(stream=sys.stderr)
logger = logging.getLogger('textlogger')
logger.setLevel(logging.DEBUG)


def start(datainqueue,dataqueue,comqueue,config={'filename':'','time':True,'host':True,'device':True,'newline':False,'pcktcnt':False,'keys':['data']}):
    funcname = __name__ + '.start()'
    logger.debug(funcname + ':Opening writing:')
    filename = config['filename']
    fs = []
    if True:
        try:
            f = open(filename,'w+')
            fs.append(f)
            logger.debug(funcname + 'Opened file: {:s}'.format(filename))            
        except Exception as e:
            logger.warning(funcname + ': Error opening file:' + filename + ':' + str(e))
            return
    
    bytes_written   = 0
    packets_written = 0
    while True:
        try:
            com = comqueue.get(block=False)
            logger.debug(funcname + ': received:' + str(com))
            # Closing all open files
            try:
                for f in fs:
                    f.close()
            except Exception as e:
                logger.debug(funcname + ': could not close:' + str(f))
                
            break
        except Exception as e:
            #logger.warning(funcname + ': Error stopping thread:' + str(e))
            pass


        time.sleep(0.05)
        while(datainqueue.empty() == False):
            try:
                data = datainqueue.get(block=False)
                datastr = ''
                if(config['pcktcnt']):
                    datastr += '{:d},'.format(packets_written)
                if(config['time']):
                    tstr = datetime.datetime.fromtimestamp(data['t']).strftime('%Y-%m-%d %H:%M:%S.%f')
                    datastr += tstr
                if(config['host']):
                    datastr += ',' + data['host']['addr'] + ',' + data['host']['name']
                if(config['device']):
                    datastr += ',' + data['device']

                for key in config['keys']:
                    datastr +=  ',' + key + ',' + str(data[key])

                if(config['newline']):                    
                    datastr += '\n'
                print('Datastr',datastr)
                bytes_written += len(datastr)
                packets_written += 1
                for f in fs:
                    f.write(datastr)
                    f.flush()
                    
                    
                data_new = data
                data_new['data'] = datastr
                data_new['bytes_written']   = bytes_written
                data_new['packets_written'] = packets_written                
                dataqueue.put(data_new)
                #print('Read data',datastr)

            except Exception as e:
                logger.debug(funcname + ':Exception:' + str(e))
                #print(data)

class Device():
    def __init__(self,dataqueue=None,comqueue=None,datainqueue=None,filename = ''):
        """
        """
        self.publish     = True  # publishes data, a typical device is doing this
        self.subscribe   = True  # subscribing data, a typical datalogger is doing this
        self.datainqueue = datainqueue
        self.dataqueue   = dataqueue        
        self.comqueue    = comqueue
        self.config      = {}
        self.config['filename']    = ''
        self.config['host']    = True
        self.config['time']    = True
        self.config['device']  = True
        self.config['newline'] = False
        self.config['keys']    = ['data']
                
    def start(self):
        config=copy.deepcopy(self.config)
        start(self.datainqueue,self.dataqueue,self.comqueue,config=config)
        
    def __str__(self):
        sstr = 'textlogger'
        return sstr



#
#
# The init widget
#
#


class initDeviceWidget(QtWidgets.QWidget):
    device_start = QtCore.pyqtSignal(Device) # Signal requesting a start of the device (starting the thread)
    device_stop  = QtCore.pyqtSignal(Device) # Signal requesting a stop of device
    connect      = QtCore.pyqtSignal(Device) # Signal requesting a connect of the datainqueue with available dataoutqueues of other devices
    def __init__(self,device=None):
        super(QtWidgets.QWidget, self).__init__()
        layout        = QtWidgets.QGridLayout(self)
        self.device   = device
        self.label    = QtWidgets.QLabel("Textlogger setup")
        self.config_widgets= [] # A list of all widgets that can only be used of the device is not started yet
        # Input output widget
        self.inout    = QtWidgets.QWidget()
        inlayout      = QtWidgets.QHBoxLayout(self.inout)
        # Input widget
        vinlayout     = QtWidgets.QFormLayout()
        self.inlabel  = QtWidgets.QLabel("Input") 
        self.inlist   = QtWidgets.QTreeWidget()
        self.inlist.setColumnCount(1)
        self.inlist.setHeaderLabels(["Name"])                 
        vinlayout.addRow(self.inlabel)         
        vinlayout.addRow(self.inlist)         
        self.adddeviceinbtn   = QtWidgets.QPushButton("Add/Rem device")
        self.adddeviceinbtn.clicked.connect(self.con_clicked)                
        vinlayout.addRow(self.adddeviceinbtn)
        self.config_widgets.append(self.adddeviceinbtn)       
        # The output tree widget
        voutlayout    = QtWidgets.QFormLayout()
        self.outlabel = QtWidgets.QLabel("Logfile")
        self.outfilename = QtWidgets.QLineEdit()        
        voutlayout.addRow(self.outlabel)
        voutlayout.addRow(self.outfilename)
        self.addfilebtn   = QtWidgets.QPushButton("Add file")
        self.config_widgets.append(self.addfilebtn)       
        self.addfilebtn.clicked.connect(self.get_filename)
        voutlayout.addRow(self.addfilebtn)
        
        inlayout.addLayout(vinlayout)         
        inlayout.addLayout(voutlayout)         
        
        # The rest
        #self.conbtn = QtWidgets.QPushButton("Connect logger to devices")
        #self.conbtn.clicked.connect(self.con_clicked)        
        self.startbtn = QtWidgets.QPushButton("Start logging")
        self.startbtn.clicked.connect(self.start_clicked)
        self.startbtn.setCheckable(True)

        self.timecheck     = QtWidgets.QCheckBox("Add time")
        self.timecheck.setChecked(True)
        self.config_widgets.append(self.timecheck)               
        self.devicecheck   = QtWidgets.QCheckBox("Add devicename")
        self.devicecheck.setChecked(True)
        self.config_widgets.append(self.devicecheck)               
        self.hostcheck     = QtWidgets.QCheckBox("Add hostname")
        self.hostcheck.setChecked(True)
        self.config_widgets.append(self.hostcheck)               
        self.newlinecheck  = QtWidgets.QCheckBox("Add newline")
        self.config_widgets.append(self.newlinecheck)
        self.newlinecheck.setChecked(True)        
        self.packetcntcheck= QtWidgets.QCheckBox("Add packet count")
        self.config_widgets.append(self.packetcntcheck)        
        self.fdataentry    = QtWidgets.QLabel("Data keys to log")        
        self.dataentry     = QtWidgets.QLineEdit()
        self.dataentry.setText('data')
        self.config_widgets.append(self.dataentry)

        # Do a regular check of the input channels and update the list if changed
        self.inputchecktimer = QtCore.QTimer()
        self.inputchecktimer.timeout.connect(self.update_device_list)
        self.inputchecktimer.start(500)
        self.data_receiver_local = self.device.data_receiver.copy()
        

        layout.addWidget(self.label,0,0)               
        layout.addWidget(self.inout,1,0,1,4) 
        layout.addWidget(self.timecheck,2,0)
        layout.addWidget(self.devicecheck,2,1)
        layout.addWidget(self.hostcheck,3,0)
        layout.addWidget(self.newlinecheck,3,1)
        layout.addWidget(self.packetcntcheck,3,2)        
        layout.addWidget(self.fdataentry,4,0)
        layout.addWidget(self.dataentry,4,1,1,3)
        layout.addWidget(self.startbtn,5,0,1,4)
        
        #layout.addRow(self.label)               
        #layout.addRow(self.inout)               
        #layout.addRow(self.timecheck,self.devicecheck)
        #layout.addRow(self.hostcheck,self.newlinecheck)
        #layout.addRow(self.fdataentry,self.dataentry)                
        #layout.addRow(self.startbtn)

    def finalize_init(self):
        """ Util function that is called by redvypr after initializing all config (i.e. the configuration from a yaml file)
        """
        self.update_device_list()

    def get_filename(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self,"Logging file","","All Files (*);;Text Files (*.txt)")
        if filename:
            self.outfilename.setText(filename)
            self.device.config['filename'] = filename

    def update_device_list(self):
        """ Regularly called function to update the list
        """
        pass
        #print('Update')
        tree = self.inlist        
        root = tree.invisibleRootItem()
        child_count = root.childCount()
        data_receivers = []
        for i in range(child_count):
            item = root.child(i)
            devicename = item.text(0)
            data_receivers.append(devicename)

        # Add new items
        for recv in self.device.data_receiver:
            add_receiver = True
            if(recv in data_receivers):
                pass
            else:
                item = QtWidgets.QTreeWidgetItem([recv,])                
                self.inlist.insertTopLevelItem(0, item)

        # Check if there are too many items, if yes, find the one
        # which has to be removed
        child_count = root.childCount()
        if(child_count > len(self.device.data_receiver)):
            for i in range(child_count):
                item = root.child(i)
                devicename = item.text(0)
                if(devicename in self.device.data_receiver):
                    pass
                else:
                    try:
                        (item.parent() or root).removeChild(item)
                    except Exception as e:
                        logger.debug(funcname + ': {:s}'.format(str(e)))                        
                    

    def con_clicked(self):
        print('Connect clicked')
        button = self.sender()
        self.connect.emit(self.device)        
            
    def start_clicked(self):
        button = self.sender()
        if button.isChecked():
            logger.debug("button pressed")
            self.device.config['time']   = self.timecheck.isChecked()
            self.device.config['host']   = self.hostcheck.isChecked()
            self.device.config['device'] = self.devicecheck.isChecked()
            self.device.config['newline']= self.newlinecheck.isChecked()
            self.device.config['pcktcnt']= self.packetcntcheck.isChecked()  
            log_keys = str(self.dataentry.text()).split(',')
            self.device.config['keys']   = log_keys
            self.device_start.emit(self.device)
        else:
            logger.debug('button released')
            self.device_stop.emit(self.device)

            
    def thread_status(self,status):
        self.update_device_list()        
        self.update_buttons(status['threadalive'])
        
    def update_buttons(self,thread_status):
            """ Updating all buttons depending on the thread status (if its alive, graying out things)
            """
            # Running
            if(thread_status):
                self.startbtn.setText('Stop')
                self.startbtn.setChecked(True)
                for w in self.config_widgets:
                    w.setEnabled(False)
            # Not running
            else:
                self.startbtn.setText('Start')
                for w in self.config_widgets:
                    w.setEnabled(True)
                    
                # Check if an error occured and the startbutton 
                if(self.startbtn.isChecked()):
                    self.startbtn.setChecked(False)
                #self.conbtn.setEnabled(True)


class displayDeviceWidget(QtWidgets.QWidget):
    def __init__(self):
        super(QtWidgets.QWidget, self).__init__()
        layout          = QtWidgets.QVBoxLayout(self)
        hlayout         = QtWidgets.QHBoxLayout()        
        self.text       = QtWidgets.QPlainTextEdit(self)
        self.text.setReadOnly(True)
        self.byteslab   = QtWidgets.QLabel("Bytes written: ")
        self.packetslab = QtWidgets.QLabel("Packets written: ")
        self.text.setMaximumBlockCount(10000)
        hlayout.addWidget(self.byteslab)
        hlayout.addWidget(self.packetslab)
        layout.addLayout(hlayout)
        layout.addWidget(self.text)
        #self.text.insertPlainText("hallo!")        

    def update(self,data):
        #print('data',data)
        self.byteslab.setText("Bytes written: {:d}".format(data['bytes_written']))
        self.packetslab.setText("Packets written: {:d}".format(data['packets_written']))
        self.text.insertPlainText(str(data['data']) + '\n')
        
