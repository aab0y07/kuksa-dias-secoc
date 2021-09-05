"""

        @ Author: Abdlhay Boydedaev
	
        This script is created on the frame of the thesis workl: "Data security for cloud based diagnosis"

        This script maps found signals puts signal authentication status to queue 


"""

# Create command to execute the script


import os
import argparse
import can
import threading
import time
import cantools
import secoc_verification

from Cryptodome.Hash import CMAC
from Cryptodome.Cipher import AES

# alternative to check "from cryptography.fernet import Fernet"




class AutosarSec:
    def __init__(self, cfg, rxqueue, mapper):
        self.queue = rxqueue
        self.cfg = cfg
        self.mapper = mapper
        self.message = ''
        self.db = cantools.database.load_file(cfg['vss.dbcfile'])
        self.canidwl = self.get_whitelist()
        #self.freshness_value = freshness_value
        self.parseErr=0
        self.transmitted_data = []
        self.tampered_signals = []
        self.nonTampered_signals = []
       
        
    
    def start_listening(self):
        #print("Open CAN device {}".format(self.cfg['can.port']))
        print("Initialize bus")
        self.bus = can.interface.Bus('vcan0', bustype='socketcan')
        rxThread = threading.Thread(target=self.rxWorker)
        rxThread.start()
        print("Thread has started")
    
    def rxWorker(self):
        calculated_mac = ''
        print("Starting thread")
        while True:
            msg=self.bus.recv()
            
            '''
            decode=self.db.decode_message(msg.arbitration_id, msg.data)
            rxTime=time.time()
            for k,v in decode.items():
                if k in self.mapper:
                    if self.mapper.minUpdateTimeElapsed(k, rxTime):
                        self.queue.put((k,v))
            '''
              
            can_data = msg.__str__()
            print('CAN data in string:', str(can_data))  
            # Autosarsecoc instance
            autosar = secoc_verification.SecocVerification(can_data)
            print('Autosar:', str(autosar))  
            auth_status = autosar.authentication_status()
            print('Authentication status:', str(auth_status))  
            #rxTime=time.time()
            for key, value in self.canidwl.items():
                print('Received values: {}, {}'.format(key, str(value)))
                for k, v in auth_status.items():
                    print('Received authvalues: {}, {}'.format(k, str(v)))
                    if value == k:
                        self.queue.put((key, v))

            
            '''
            
            for msg in self.db.messages:
                for signal in msg.signals:
                    if msg.frame_id == can_id:
                        print("Before publish to VSS: " + str(signal.name))
                        print("Before publish to VSS: " + str(msg.frame_id))
                        self.queue.put((signal.name, 1))
                        print("After publish to VSS: ")
            else: 
                print('MAC value verification has failed!')
            for key, value in self.canidwl.items():
                if value == can_id:
                    print("Before publish to VSS: " + str(key))
                    print("Before publish to VSS: " + str(can_id))
                    self.queue.put(key, 0)
                    print("After publish to VSS: ")
            '''
            
    def get_whitelist(self):
        print("Collecting signals, generating CAN ID whitelist")
        wl = {}
        for entry in self.mapper.map():
            canid=self.get_canid_for_signal(entry[0])
            print('ID: ', str(canid))
            if canid != None and canid not in wl:
                wl[entry[0]] = hex(canid)
        return wl

    def get_canid_for_signal(self, sig_to_find):
        for msg in self.db.messages:
            for signal in msg.signals:
                if signal.name == sig_to_find:
                    id = msg.frame_id
                    print("Found signal {} in CAN frame id 0x{:02x}".format(signal.name, id))
                    return id
        print("Signal {} not found in DBC file".format(sig_to_find))
        return None

   
