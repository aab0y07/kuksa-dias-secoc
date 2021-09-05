"""
        @ Author: Abdlhay Boydedaev
	
        This script is created on the frame of the thesis workl: "Data security for cloud based diagnosis"
        
        This script is created on the base of the "cloudfeeder.py" and collects  
        required data from the in-vehicle server, `kuksa-val-server`, 
        and then transmit the result to the DIAS-KUKSA cloud.


"""

import argparse
import json
import socket
import subprocess
import time
#import testclient
import kuksa_viss_client
import preprocessor_bosch

def getConfig():
    parser = argparse.ArgumentParser()
    parser.add_argument("-j", "--jwt", help="JWT security token file", type=str)
    parser.add_argument("--host", metavar='\b', help="Host URL", type=str) # "mqtt.bosch-iot-hub.com"
    parser.add_argument("-p", "--port", metavar='\b', help="Protocol Port Number", type=str) # "8883"
    parser.add_argument("-u", "--username", metavar='\b', help="Credential Authorization Username (e.g., {username}@{tenant-id} ) / Configured in \"Bosch IoT Hub Management API\"", type=str) # "pc01@t20babfe7fb2840119f69e692f184127d"
    parser.add_argument("-P", "--password", metavar='\b', help="Credential Authorization Password / Configured in \"Bosch IoT Hub Management API\"", type=str) # "junhyungki@123"
    parser.add_argument("-c", "--cafile", metavar='\b', help="Server Certificate File (e.g., iothub.crt)", type=str) # "iothub.crt"
    parser.add_argument("-t", "--type", metavar='\b', help="Transmission Type (e.g., telemetry or event)", type=str) # "telemetry"
    parser.add_argument("-r", "--resume", action='store_true', help="Resume the application with the accumulated data when restarting", default=False)
    args = parser.parse_args()
    return args

def getVISSConnectedClient(jwt):
    # 1. Create a VISS client instance
    #client = testclient.VSSTestClient()
    config = {}
    client = kuksa_viss_client.KuksaClientThread(config)
    # 2. Connect to the running viss server insecurely
    
    client.start()
    #client.do_connect("--insecure")
    
    # 3. Authorize the connection
    client.authorize(jwt)
    
    return client

def checkPath(client, path):
    val = json.loads(client.getValue(path))["value"]
    if val == "---":
        return 0
    else:
        return val

def socket_connection_on(s, host, port):
    try:
        s.connect((host, int(port))) # host and port
        print("# Socket Connected :)")
        return True
    except socket.timeout:
        print("# Socket Timeout :(")
        return False
    except socket.gaierror:
        print("# Temporary failure in name resolution :(")
        return False

def send_telemetry(host, port, comb, telemetry_queue):
    # Create a socket instance
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.1)
    if socket_connection_on(s, host, port):
        if len(telemetry_queue) != 0:
            for i in range(0, len(telemetry_queue)):
                tel = telemetry_queue.pop(0)
                p = subprocess.Popen(tel)
                print("# Popped telemetry being sent... Queue Length: " + str(len(telemetry_queue)))
                try:
                    p.wait(1)
                except subprocess.TimeoutExpired:
                    p.kill()
                    telemetry_queue.insert(0, tel)
                    print("\n# Timeout, the popped telemetry collected. Queue Length: " + str(len(telemetry_queue)))
                    telemetry_queue.append(comb)
                    print("# The current telemetry also collected. Queue Length: " + str(len(telemetry_queue)))
                    return
                except socket.gaierror:
                    s.close()
                    telemetry_queue.insert(0, tel)
                    print("\n# Temporary failure in name resolution, the popped telemetry collected. Queue Length: " + str(len(telemetry_queue)))
                    telemetry_queue.append(comb)
                    print("# The current telemetry also collected. Queue Length: " + str(len(telemetry_queue)))
                    return
                print("# Successfully done!\n")
        p = subprocess.Popen(comb)
        print("# Current telemetry being sent...")
        try:
            p.wait(1)
        except subprocess.TimeoutExpired:
            p.kill()
            telemetry_queue.append(comb)
            print("\n# Timeout, the current telemetry collected. Queue Length: " + str(len(telemetry_queue)))
            return
        except socket.gaierror:
            s.close()
            telemetry_queue.append(comb)
            print("\n# Temporary failure in name resolution, the current telemetry collected. Queue Length: " + str(len(telemetry_queue)))
            return
        print("# Successfully done!\n")
    else:
        telemetry_queue.append(comb)
        print("# The current telemetry collected, Queue Length: " + str(len(telemetry_queue)))

print("kuksa.val cloud example feeder")

# Get the pre-fix command for publishing data
args = getConfig()

# Get a VISS-server-connected client
client = getVISSConnectedClient(args.jwt)

# Create a BinInfoProvider instance
# binPro = preprocessor_bosch.BinInfoProvider()

# buffer for mqtt messages in case of connection loss or timeout
telemetry_queue = []

'''
if args.resume:
    print("Resuming accumulated data....")
    telemetry_queue = load_data(binPro, telemetry_queue)
    print("Queue Length: " + str(len(telemetry_queue)))
'''    

while True:
    # 1. Time delay
    time.sleep(0.8)
    print("\n\n\n")
    kuksa_val_dict = {}
    
    # Fresh target 
    kuksa_val_dict["IsAmbientAirTempAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsAmbientAirTempAuthenticated") # Missing (Not available in EDC17 but MD1)(19/11/2020)
    kuksa_val_dict["IsAftrtrtmnt1SCRCtlystIntkGasTempAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsAftrtrtmnt1SCRCtlystIntkGasTempAuthenticated")
    kuksa_val_dict["IsAftrtratment1ExhaustGasMassFlowAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsAftrtratment1ExhaustGasMassFlowAuthenticated")
    kuksa_val_dict["IsAftertreatment1IntakeNOxAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsAftertreatment1IntakeNOxAuthenticated")
    kuksa_val_dict["IsAftertreatment1OutletNOxAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsAftertreatment1OutletNOxAuthenticated")
    
    kuksa_val_dict["IsTimeSinceEngineStartAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsTimeSinceEngineStartAuthenticated")
    kuksa_val_dict["IsActualEngPercentTorqueAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsActualEngPercentTorqueAuthenticated")
    kuksa_val_dict["IsEngReferenceTorqueAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsEngReferenceTorqueAuthenticated")
    kuksa_val_dict["IsNominalFrictionPercentTorqueAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsNominalFrictionPercentTorqueAuthenticated")
    kuksa_val_dict["IsEngSpeedAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsEngSpeedAuthenticated")
    kuksa_val_dict["IsEngSpeedAtIdlePoint1Authenticated"] = checkPath(client, "Vehicle.Authentication.IsEngSpeedAtIdlePoint1Authenticated")
    kuksa_val_dict["IsEngSpeedAtPoint2Authenticated"] = checkPath(client, "Vehicle.Authentication.IsEngSpeedAtPoint2Authenticated")
    kuksa_val_dict["IsBarometricPressAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsBarometricPressAuthenticated")
    kuksa_val_dict["IsEngCoolantTempAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsEngCoolantTempAuthenticated")
    kuksa_val_dict["IsEngPercentLoadAtCurrentSpeedAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsEngPercentLoadAtCurrentSpeedAuthenticated")
    kuksa_val_dict["IsProtectLampStatusAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsProtectLampStatusAuthenticated")
    kuksa_val_dict["IsRedStopLampStateAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsRedStopLampStateAuthenticated")
    kuksa_val_dict["IsAmberWarningLampStatusAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsAmberWarningLampStatusAuthenticated")
    kuksa_val_dict["IsMalfunctionIndicatorLampStatusAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsMalfunctionIndicatorLampStatusAuthenticated")
    kuksa_val_dict["IsFlashAmberWarningLampAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsFlashAmberWarningLampAuthenticated")
    kuksa_val_dict["IsFlashMalfuncIndicatorLampAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsFlashMalfuncIndicatorLampAuthenticated")
    kuksa_val_dict["IsFlashProtectLampAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsFlashProtectLampAuthenticated")
    kuksa_val_dict["IsFlashRedStopLampAuthenticated"] = checkPath(client, "Vehicle.Authentication.IsFlashRedStopLampAuthenticated")
    # Fresh target
    

    # 6. Format telemetry
    tel_json = json.dumps(kuksa_val_dict)
    # Sending device data via Mosquitto_pub (MQTT - Device to Cloud)
    comb =['mosquitto_pub', '-d', '-h', args.host, '-p', args.port, '-u', args.username, '-P', args.password, '--cafile', args.cafile, '-t', args.type, '-m', tel_json]

    # 7. MQTT: Send telemetry to the cloud. (in a JSON format)
    send_telemetry(args.host, args.port, comb, telemetry_queue)

    # 8. Saving telemetry dictionary
    #save_data(binPro, telemetry_queue)

    # B. Do not sample data if the aftertreatment system is not ready
    #else:
    print("\n# One or both NOx sensors is(are) not ready (default value: 3012.75).\n# No bin sampling.")
