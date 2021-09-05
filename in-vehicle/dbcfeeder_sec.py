#!/usr/bin/python3

########################################################################
# Copyright (c) 2020 Robert Bosch GmbH
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0
########################################################################


import sys
import argparse
import configparser
import queue

import dbc2vssmapper
import dbcreader
import j1939reader
import websocketconnector
import elm2canbridge


import queue
import autosar_sec


cfg = {}

def getConfig():
    global cfg
    # argparse is used to write CLI 
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", help="CAN port. Choose \"elmcsn\" for ELM adapter", type=str)

    parser.add_argument("--obdbaudrate", help="Baudrate to ELM if CAN port is \"elmcan\"", type=int)
    parser.add_argument("--obdcanspeed", help="CAN bus speed if CAN port is \"elmcan\"", type=int)
    parser.add_argument("--noobdcanack",
                        help="Do not acknowledge CAN messages be  Only if CAN port is \"elmcan\"",  dest='nocanack_override', action='store_true')
    parser.add_argument("--obdcanack",
                        help="Acknowledge CAN messages be  Only if CAN port is \"elmcan\"",  dest='canack_override', action='store_true')



    parser.add_argument("--obdport", help="Serial port where ELM is connected. Only if CAN port is \"elmcan\"",
                        type=str)

    parser.add_argument("--dbc", help="DBC file used to parse CAN messages", type=str)

    parser.add_argument("-s", "--server", help="VSS server", type=str)
    parser.add_argument("-j", "--jwt", help="JWT security token file", type=str)
    parser.add_argument("--mapping", help="VSS mapping file", type=str)
    parser.add_argument("--j1939", action='store_true', help="(Optional) Enable SAE-J1939 Mode. Normal_Mode: ignore, J1939_Mode: \'--j1939\' (No argument needed after)")

    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read('config.ini')

    vsscfg = config['vss']
    cfg['vss.server'] = vsscfg.get("server", "ws://localhost:8090")
    if args.server:
        cfg['vss.server'] = args.server

    cfg['vss.jwttoken'] = vsscfg.get("jwttoken", "jwt.token")
    if args.jwt:
        cfg['vss.jwttoken'] = args.jwt

    cfg['vss.mapping'] = vsscfg.get("mapping", "mapping.yaml")
    if args.mapping:
        cfg['vss.mapping'] = args.mapping

    cfg['vss.dbcfile'] = vsscfg.get("dbcfile", "example.dbc")
    if args.dbc:
        cfg['vss.dbcfile'] = args.dbc

    cancfg = config['can']
    cfg['can.port'] = cancfg.get("port", "can0")
    if args.device:
        cfg['can.port'] = args.device

    cfg['can.j1939'] = cancfg.getboolean("j1939", False)
    if args.j1939:
    	cfg['can.j1939'] = args.j1939

    elmcfg = config['elmcan']
    cfg['elm.port'] = elmcfg.get("port", "/dev/ttyS0")
    if args.obdport:
        cfg['elm.port'] = args.obdport

    cfg['elm.baudrate'] = elmcfg.getint("baudrate", 2000000)
    if args.obdbaudrate:
        cfg['elm.baudrate'] = args.obdbaudrate

    cfg['elm.canspeed'] = elmcfg.getint("speed", 500000)
    if args.obdcanspeed:
        cfg['elm.canspeed'] = args.obdcanspeed

    cfg['elm.canack'] = elmcfg.getboolean("canack", False)

    # Can override CAN ACK setting from commandline. Safe choice, no ack, is dominant
    if args.canack_override:
        cfg['elm.canack'] = True
    if args.nocanack_override:
        cfg['elm.canack'] = False


def publishData(vss):
    print("Publish data")
    for obdval, config in mapping.map():

        if config['value'] is None:
            continue
        print("Publish {}: to ".format(obdval), end='')
        for path in config['targets']:
            vss.push(path, config['value'].magnitude)
            print(path, end=' ')
        print("")


print("kuksa.val DBC example feeder")
getConfig()

print("VSS server           : {}".format(cfg['vss.server']))
print("JWT token file       : {}".format(cfg['vss.jwttoken']))
print("DBC  file            : {}".format(cfg['vss.dbcfile']))
print("VSS mapping file     : {}".format(cfg['vss.mapping']))
print("CAN port             : {}".format(cfg['can.port']))
print("J1939 mode           : {}".format(cfg['can.j1939']))
if cfg['can.port'] == "elmcan":
    print("ELM serial port     : {}".format(cfg['elm.port']))
    print("ELM serial baudrate : {}".format(cfg['elm.baudrate']))
    print("ELM CAN Speed       : {}".format(cfg['elm.canspeed']))
    print("ELM Ack CAN frames  : {}".format(cfg['elm.canack']))


with open(cfg['vss.jwttoken'], 'r') as f:
    token = f.readline().rstrip('\n')

mapping = dbc2vssmapper.mapper(cfg['vss.mapping'])

vss = websocketconnector.vssclient(cfg['vss.server'], token)
can_auth_queue = queue.Queue()


# Create AutosarSecOC instance
secoc = autosar_sec.AutosarSec(cfg,can_auth_queue,mapping)
#if cfg['can.port'] == 'elmcan':
#print("Using elmcan. Trying to set up elm2can bridge")
#elmbr=elm2canbridge.elm2canbridge(cfg, secoc.canidwl)
secoc.start_listening()
   

while True:
    signal, auth_value = can_auth_queue.get()
    print("Update signal auth_status {} to {}".format(signal, auth_value))
    for auth_target in mapping[signal]['auth_status']:
        print("Publish auth_status {} to {}".format(signal,auth_target))
        vss.push(auth_target, auth_value)


sys.exit(0)
