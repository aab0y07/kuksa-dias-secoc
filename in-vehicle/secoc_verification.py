"""

This script is to authenticate CAN messages on the base of Autosar SecOC module

        hexSecKey = "2b7e151628aed2a6abf7158809cf4f3c"
        secret= bytearray.fromhex(hexSecKey)
        cobj = CMAC.new(secret, ciphermod=AES)
        hexMes = "aabbccdd010000000000000000000000"
        byteMes= bytearray.fromhex(hexMes)
        cobj.update(byteMes)

        print (cobj.hexdigest())


"""

# Create command to execute the script


import os
import argparse
import can
import threading
import time
import cantools

from Cryptodome.Hash import CMAC
from Cryptodome.Cipher import AES

# alternative to check "from cryptography.fernet import Fernet"




class SecocVerification:
	freshness_counter = 0x0000
	def __init__(self,can_frame):
		self.frame=can_frame
		self.secret_key = "2b7e151628aed2a6abf7158809cf4f3c"  

	def get_frame_id(self):
		can_frame_id = '0x' + self.frame[36:44]
		return can_frame_id
		
	def get_frame_data(self):
		can_frame_data = '0x' + self.frame[-42:-18]
		return can_frame_data.replace(' ', '')  
	
	def format_frame_data(self):
		data_in_str = self.get_frame_data()
		data_in_int = int(data_in_str, 16)
		received_frame_data = hex(data_in_int)
		print('Received frame data: ', received_frame_data)
		return received_frame_data
	
	def authentication_status(self):
		auth_dict = {}
		received_frame = self.format_frame_data()
		transmitted_mac_val = received_frame[12:]
		print('Received MAC value: ',transmitted_mac_val)
        
		calculated_mac_val = self.verify_frame(received_frame)
		print('Calculated MAC value: ',calculated_mac_val)

		can_id = self.get_frame_id()
		# Compare transmitted and calculated MAC values
		if calculated_mac_val == transmitted_mac_val:
			CmacAes128.freshness_counter += 1
			print('Incremented FV value: ' , self.freshness_counter)
			print('MAC value has been verified successfully!')
			auth_dict[can_id] = 1     
		else: 
			print('MAC value verification has failed!')
			auth_dict[can_id] = 0
			# Apply here failed FV logic
		return auth_dict
        
        
	def calculate_complete_freshness(self, can_frame):
        #for element in arr:
        # Get access to array element's 5th byte
		counter_to_convert = can_frame[10:12]
		print('Before: ', counter_to_convert)
		a = int(counter_to_convert,16)
		truncated_counter = hex(a)
        #print('After: ', str(truncated_counter))
        #print('Truncated counter: ', truncated_counter)
		pi_counter_lsb = hex((self.freshness_counter&(0xFF<<(8*0)))>>(8*0))[2:]
		print('Pi counter LSB: ', pi_counter_lsb)
		pi_counter_msb = hex((self.freshness_counter&(0xFF<<(8*1)))>>(8*1))[2:]
		print('Pi counter MSB:', str(pi_counter_msb))
		print("Value of Tc: ", str(truncated_counter))
		print("Type of Fc: ", type(self.freshness_counter))
		if truncated_counter > hex(self.freshness_counter):
            # Need to be clarified, especially byte order does not work yet
			complete_counter_1 = "0x" + pi_counter_msb + truncated_counter[2:] 
			a = int(complete_counter_1,16)
			hex_n = "{0:#0{1}x}".format(a,6)
			print('Complete counter if:', hex_n)
		else:
			temp_counter_val = "0x" + pi_counter_msb
			a = int(temp_counter_val,16) + 0x1
			hex_n = hex(a)
			complete_counter_2 =  "0x" + hex_n[2:] + truncated_counter[2:]
            
			a = int(complete_counter_2,16)
			hex_n = "{0:#0{1}x}".format(a,6)
			print('Complete counter else:', hex_n)
		return hex_n
            


	def access_nth_byte(target, n):
		return hex((target&(0xFF<<(8*n)))>>(8*n))
    
	def assign_cipher(self, can_frame):
		complete_freshness_val = ''
		complete_counter_val = self.calculate_complete_freshness(can_frame)[2:]
		print('Received CFV: ', complete_counter_val)
		res1 = can_frame[2:10]
        # 1. Get complete_freshness_value
        # 2. Retrieve the message from transmitted CAN frame
		res = res1 + complete_counter_val
		self.message = res.ljust(20 + len(res), '0')
		print('Assigned message : ', self.message)
		return self.message
        
	def generate_mac(self, can_frame):
		trunc_calc_mac = ''
		self.message = self.assign_cipher(can_frame)
		if ''.__eq__(self.secret_key) or ''.__eq__(self.message):
			print('Key or message cannot be empty!')
			return -1
		if len(self.secret_key) < 32 or len(self.message) < 32:
			print('Key or message length is less than 16 byte')
			return -1
		secret= bytearray.fromhex(self.secret_key)
		cobj = CMAC.new(secret, ciphermod=AES)
		byteMes= bytearray.fromhex(self.message)
		cobj.update(byteMes)
		calculated_mac = cobj.hexdigest()
		print ('Calculated mac: ', calculated_mac)
        # truncate the MAC before return
		trunc_calc_mac = calculated_mac[0:6]
		print ('Truncated mac: ', trunc_calc_mac)
		return trunc_calc_mac
        
	def verify_frame(self, can_frame):
		return self.generate_mac(can_frame)
            
	'''
	def authenticated_signals(self):
        print("Method to return authenticated signals")
        
        auth_signals = {
          "AmbientAirTemp": 0,
          "Aftrtrtmnt1SCRCtlystIntkGasTemp": 1,
          "Aftrtratment1ExhaustGasMassFlow": 0,
          "Aftertreatment1IntakeNOx": 0,
          "Aftertreatment1OutletNOx": 0,
          "TimeSinceEngineStart": 0,
          "ActualEngPercentTorque": 0,
          "EngReferenceTorque": 0,
          "NominalFrictionPercentTorque": 0,
          "EngSpeed": 0,
          "EngSpeedAtIdlePoint1": 0,
          "EngSpeedAtPoint2": 0,
          "BarometricPress": 0,
          "EngCoolantTemp": 0,
          "EngPercentLoadAtCurrentSpeed": 0,
          "MalfunctionIndicatorLampStatus": 0 
        }
        return auth_signals
	'''
