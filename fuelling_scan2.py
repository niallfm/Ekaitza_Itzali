# -*- coding: UTF-8 -*-
# BSD 2-Clause License

# Copyright (c) 2017, xabiergarmendia@gmail.com
# All rights reserved.
#
# Code used:
# https://github.com/pajacobson/td5keygen by paul@discotd5.com

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
  # list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
  # this list of conditions and the following disclaimer in the documentation
  # and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Ekaitza Itzali
# by EA2EGA
#
# Must be used with a CP2102 USB to TTL converter.
# The CP2102 must be set up for 360 bauds instead of 300
# and 10400 bauds instead of 14400.
# This can be done with the AN205SW tool from Silicon Labs,
# the manufacturer of the CP2102
#
# Schematic:
#
# The first version of the circuit had poor noise inmunity
# This version have changed some resistance values and added a 
# high frecuency noise filtering capacitor.
# No the number of chesum errors is negligible.
#
#         Car Obd Port       |       CP2102 USB to TTL converter
#                            |
# K-line      12 Volt   GND  |  GND   5 Volt    RX        TX
#  |           |         |       |     |         |        |
#  |           |     |---|-------|     |         |        |
#  |           |     |                 |         |        |
#  |--510------|     | Reduce signal   |         |        |
#  |                 |       to 0-5V   |         |        |
#  |        |--100pF-|             |         |        |
#  |        |                          |         |        |
#  |--2K2--------1N4184->--------------|         |        |
#  |        |                                    |        |
#  |        |------------------------------------|        |
#  |                                                      |
#  |                                                      |
#  |     2N2222A              (Invert again and Power)    |
#  |     C  B  E                                          |
#  |     |  |  |-------GND                                |
#  |------  |                                             |
#           |                                             |
#           |--------|                                    |
#                    |                                    |
#       5 Volt       |  2N2222A      (Inverter)           |
#          |-----2K2----C  B  E                           |
#                          |  |----- GND                  |
#                          |                              |
#                          |------------------2K2---------|


import time
import serial
from math import *
import os
import logging, sys

debug = 5;
interframe_delay=0.02
serial_port = 'COM3'

b_voltage=0
rpm=0
rpm_error=0
speed=0
t_coolant=0
t_air=0
t_ext=0
t_fuel =0
p1=0
p2=0
p3=0
p4=0
supply = 0
aap=0
maf =0
ap1=0
ap2=0
pb1=0
pb2=0
pb3=0
pb4=0
pb5=0

def fast_init():
    ser = serial.Serial(serial_port, 300, timeout=0.1) #CP210x is configured for 300 being 360
    command=b"\x00"
    ser.write(command) #Send a 25ms pulse
    time.sleep(0.05)
    ser.close()

def send_packet(data,res_size):
    global debug
    time.sleep(interframe_delay)
    
    lendata=len(data)
    
    modulo=0
    for i in range(0,lendata):
        modulo = modulo + ord(data[i]) 
    modulo = modulo % 256
    
    to_send=data+chr(modulo)
    ser.write(to_send)
    time.sleep(interframe_delay)

    ignore=len(to_send)
    read_val = ser.read(len(to_send)+res_size)

    read_val_s = read_val[0:ignore]
    if debug > 2:    
        print "Data Sent: %s." % ":".join("{:02x}".format(ord(c)) for c in read_val_s)
    read_val_r = read_val[ignore:]
    if debug > 2: 
        print "Data Received: %s." % ":".join("{:02x}".format(ord(c)) for c in read_val_r)
    
    modulo=0
    for i in range(0,len(read_val_r)-1):
        modulo = modulo + ord(read_val_r[i]) 
    modulo = modulo % 256
    
    if (len(read_val_r)>2):
        if (modulo!=ord(read_val_r[len(read_val_r)-1])): #Checksum error
            read_val_r=""
            if debug > 1:
                print "Checksum ERROR"
       
    return read_val_r

def seed_key(read_val_r):
    # seed = read_val_r[3:5]
    # if debug > 1:
        # print "\tSeed is: %s." % ":".join("{:02x}".format(ord(c)) for c in seed)
    # seed_int=ord(seed[0])*256+ord(seed[1])
    # if debug > 1:
        # print "\tSeed integer: %s." % seed_int

    # counter=0

    # key=[]

    # with open("key.txt") as f:
        # for line in f:
            # if (counter==seed_int):
                # content = int(line,16)
                # if debug > 1:
                    # print "\tKey integer: %s." % content
                # hex_1=int(line[0:2],16)
                # hex_2=int(line[2:4],16)
                # key=chr(hex_1)+chr(hex_2)
                # if debug > 1:
                    # print "\tKey hex: %s." % ":".join("{:02x}".format(ord(c)) for c in key)
            
            
            # counter=counter+1
    

    # key_answer=b"\x04\x27\x02"+key
    # return key_answer
    
    seed = read_val_r[3:5]
    if debug > 1:
        print "\tSeed is: %s." % ":".join("{:02x}".format(ord(c)) for c in seed)
    
    seed_int=ord(seed[0])*256+ord(seed[1])
    if debug > 1:
        print "\tSeed integer: %s." % seed_int
    
    seed=seed_int

    count = ((seed >> 0xC & 0x8) + (seed >> 0x5 & 0x4) + (seed >> 0x3 & 0x2) + (seed & 0x1)) + 1

    idx = 0
    while (idx < count):
            tap = ((seed >> 1) ^ (seed >> 2 ) ^ (seed >> 8 ) ^ (seed >> 9)) & 1
            tmp = (seed >> 1) | ( tap << 0xF)
            if (seed >> 0x3 & 1) and (seed >> 0xD & 1):
                    seed = tmp & ~1
            else:
                    seed = tmp | 1

            idx = idx + 1

    if (seed<256):
        high=0x00
        low=seed
    else:
        high=seed/256
        low=seed%256

    key=chr(high)+chr(low)
    if debug > 1:
        print "\tKey hex: %s." % ":".join("{:02x}".format(ord(c)) for c in key)
        
    key_answer=b"\x04\x27\x02"+key
    
    return key_answer

def get_rpm():
    global rpm
    response=send_packet(b"\x02\x21\x09",6)
    if len(response)<6:
        #rpm=0
        i=0
    else:
        rpm=ord(response[3])*256+ord(response[4])
    
    return rpm
    
def get_rpm_error():
    global rpm_error
    response=send_packet(b"\x02\x21\x21",6)
    if len(response)<6:
        #rpm_error=0
        i=0
    else:
        rpm_error=ord(response[3])*256+ord(response[4])
    
    if rpm_error>32768:
        rpm_error=rpm_error-65537
    return rpm_error
    
def get_bvolt():
    global b_voltage
    response=send_packet(b"\x02\x21\x10",8)
    if len(response)<8:
        #b_voltage=0
        i=0
    else:
        b_voltage=ord(response[3])*256+ord(response[4])
        b_voltage=float(b_voltage)/1000
    
    
    
    return b_voltage
    
def get_speed():
    global speed
    response=send_packet(b"\x02\x21\x0D",5)
    if len(response)<5:
        #speed=0
        i=0
    else:
        speed=ord(response[3])
        
    return speed
    
def get_temps():
    global t_coolant, t_air, t_ext, t_fuel
    response=send_packet(b"\x02\x21\x1A",20)
    if len(response)<20:
        # t_coolant=0
        # t_air=0
        # t_ext=0
        # t_fuel=0
        i=0
    else:
       t_coolant=float(ord(response[3])*256+ord(response[4]))/10-273.2
       t_air=float(ord(response[7])*256+ord(response[8]))/10-273.2
       t_ext=float(ord(response[11])*256+ord(response[12]))/10-273.2
       t_fuel=float(ord(response[15])*256+ord(response[16]))/10-273.2
        
    return t_coolant, t_air, t_ext, t_fuel
    
def get_throttle():
    global p1, p2, p3, p4, supply
    response=send_packet(b"\x02\x21\x1B",14)
    if len(response)<14:
        # p1=0
        # p2=0
        # p3=0
        # p4=0
        # supply=0
        i=0
    else:
        p1=float(ord(response[3])*256+ord(response[4]))/1000
        p2=float(ord(response[5])*256+ord(response[6]))/1000
        p3=float(ord(response[7])*256+ord(response[8]))/1000
        p4=float(ord(response[9])*256+ord(response[10]))/1000
        supply=float(ord(response[11])*256+ord(response[12]))/1000
    
    
    return p1, p2, p3, p4, supply
    
def get_aap_maf():
    global aap, maf
    debug=5
    response=send_packet(b"\x02\x21\x1C",12)
    if len(response)<12:
        #aap=0
        #maf=0   #?? Is ok?
        i=0
    else:
        aap=float(ord(response[3])*256+ord(response[4]))/10000
        maf=ord(response[7])*256+ord(response[8])
       
    return aap, maf
    
def get_pressures():
    global ap1, ap2
    debug=5
    response=send_packet(b"\x02\x21\x23",8)
    if len(response)<8:
        #ap1=0
        #ap2=0   #?? Is ok?
        i=0
    else:
        ap1=float(ord(response[3])*256+ord(response[4]))/10000
        ap2=float(ord(response[5])*256+ord(response[6]))/10000
       
    return ap1, ap2
    
def get_power_balance():
    global pb1, pb2, pb3, pb4, pb5
    response=send_packet(b"\x02\x21\x40",14)
    if len(response)<14:
        # pb1=0
        # pb2=0
        # pb3=0
        # pb4=0
        # pb5=0
        i=0
    else:
        pb1=ord(response[3])*256+ord(response[4])
        pb2=ord(response[5])*256+ord(response[6])
        pb3=ord(response[7])*256+ord(response[8])
        pb4=ord(response[9])*256+ord(response[10])
        pb5=ord(response[11])*256+ord(response[12])
       
    if pb1>32768:
        pb1=pb1-65537
    if pb2>32768:
        pb2=pb2-65537
    if pb3>32768:
        pb3=pb3-65537
    if pb4>32768:
        pb4=pb4-65537
    if pb5>32768:
        pb5=pb5-65537
        
    return pb1,pb2,pb3,pb4,pb5
    
    
os.system("cls")
print ""
print ""
print "\t\t Land Rover Td5 Storm - Fuelling Scanning"
print ""
print "Initing..."

fast_init()

ser = serial.Serial(serial_port, 10400, timeout=0.1)    #CP210x must be configured for 

time.sleep(0.1)
response=send_packet(b"\x81\x13\xF7\x81",5)             #Init Frame
time.sleep(0.1)
response=send_packet(b"\x02\x10\xA0",3)             #Start Diagnostics
time.sleep(0.1)
response=send_packet(b"\x02\x27\x01",6)             #Seed Request

if (len(response)==6):
    key_ans=seed_key(response)
    response=send_packet(key_ans,4)             #Seed Request

time.sleep(0.1)
response=send_packet(b"\x02\x21\x02",15)             #Start Diagnostics

time.sleep(0.5)

values_to_print=[None]*128

#Start requesting data
while (True):

    
    os.system("cls")
    print "\t\t Td5 Storm"
    print " "
    for i in values_to_print:
        print i
    values_to_print=[]
    #response=send_packet(b"\x02\x21\x00",30)    # 7f Error response
    # response=send_packet(b"\x02\x21\x01",6)    #
    # try:
        # values_to_print[ord(response[2])]=ord(response[3])*256+ord(response[4])
    # except:
        # err=1
    # #response=send_packet(b"\x02\x21\x02",30)    # 7f Error response ¿Start Fuelling Req?
    # response=send_packet(b"\x02\x21\x03",6)    #?
    # try:
        # values_to_print[ord(response[2])]=ord(response[3])*256+ord(response[4])
    # except:
        # err=1
    # response=send_packet(b"\x02\x21\x04",6)    #?
    # try:
        # values_to_print[ord(response[2])]=ord(response[3])*256+ord(response[4])
    # except:
        # err=1
    # response=send_packet(b"\x02\x21\x05",6)    #?
    # try:
        # values_to_print[ord(response[2])]=ord(response[3])*256+ord(response[4])
    # except:
        # err=1
    # #response=send_packet(b"\x02\x21\x06",30)    # 7f Error response
    # response=send_packet(b"\x02\x21\x07",6)    #?
    # try:
        # values_to_print[ord(response[2])]=ord(response[3])*256+ord(response[4])
    # except:
        # err=1
    # #response=send_packet(b"\x02\x21\x08",30)    # 7f Error response
    response=send_packet(b"\x02\x21\x09",6)    #RPM
    try:
        values_to_print.append(ord(response[3])*256+ord(response[4]))
    except:
        err=1
    #response=send_packet(b"\x02\x21\x0A",30)    # 7f Error response
    #response=send_packet(b"\x02\x21\x0B",30)    # 7f Error response
    #response=send_packet(b"\x02\x21\x0C",30)    # 7f Error response
    #response=send_packet(b"\x02\x21\x0D",5)    #Speed
    #response=send_packet(b"\x02\x21\x0E",20)    #? Nothing changes
    
    
    #response=send_packet(b"\x02\x21\x0F",30)    # 7f Error response
    # response=send_packet(b"\x02\x21\x10",8)    #Battery
    # #response=send_packet(b"\x02\x21\x11",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x12",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x13",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x14",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x15",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x16",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x17",30)    # 7f Error response
    # response=send_packet(b"\x02\x21\x18",5)    #?Fixed val
    # #response=send_packet(b"\x02\x21\x19",30)    # 7f Error response
    # response=send_packet(b"\x02\x21\x1A",20)    #Temperatures
    # response=send_packet(b"\x02\x21\x1B",12)    #Throttle
    # response=send_packet(b"\x02\x21\x1C",12)    #Pressure1
    # response=send_packet(b"\x02\x21\x1D",22)    #Fuelling parameters
    # for i in range (3,21,2):
        # try:
            # value=ord(response[i])*256+ord(response[i+1])
            # if value>32768:
                # value=value-65537
            # values_to_print.append(value)
        # except:
            # err=1
    #response=send_packet(b"\x02\x21\x1E",6)    #? No cambia
    # response=send_packet(b"\x02\x21\x1F",7)    #? No cambia
    #response=send_packet(b"\x02\x21\x20",8)    #
    # response=send_packet(b"\x02\x21\x21",6)    #RPM Error
    # #response=send_packet(b"\x02\x21\x22",30)    # 7f Error response
    # response=send_packet(b"\x02\x21\x23",8)    # Pressures (filer box?)
    
    # response=send_packet(b"\x02\x21\x24",6)    #? Fixed at 393
    
    # #response=send_packet(b"\x02\x21\x25",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x26",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x27",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x28",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x29",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x2A",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x2B",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x2C",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x2D",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x2E",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x2F",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x30",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x31",30)    # 7f Error response
    #response=send_packet(b"\x02\x21\x32",28)    #? Fixed values...
    
    # response=send_packet(b"\x02\x21\x33",20)    #? Fixed values...
    # #response=send_packet(b"\x02\x21\x34",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x35",30)    # 7f Error response
    # response=send_packet(b"\x02\x21\x36",6)    #? Fixed val
    # response=send_packet(b"\x02\x21\x37",6)    #? Fixed val
    # response=send_packet(b"\x02\x21\x38",6)    #? Fixed val
    # response=send_packet(b"\x02\x21\x39",5)    #? Fixed val
    # #response=send_packet(b"\x02\x21\x3A",30)    # 7f Error response
    # response=send_packet(b"\x02\x21\x3B",39)    #? Fixed values

    response=send_packet(b"\x02\x21\x3C",12)    #?
    for i in range (3,11,2):
        try:
            value=ord(response[i])*256+ord(response[i+1])
            if value>32768:
                value=value-65537
            values_to_print.append(value)
        except:
            err=1
    # response=send_packet(b"\x02\x21\x3D",22)    #?
    for i in range (3,21,2):
        try:
            value=ord(response[i])*256+ord(response[i+1])
            if value>32768:
                value=value-65537
            values_to_print.append(value)
        except:
            err=1
    # response=send_packet(b"\x02\x21\x3E",27)    #?
    # response=send_packet(b"\x02\x21\x3F",8)    #?
    # response=send_packet(b"\x02\x21\x40",14)    #Power Balance
    # #response=send_packet(b"\x02\x21\x41",30)    # 7f Error response
    # response=send_packet(b"\x02\x21\x42",8)    #?
    # response=send_packet(b"\x02\x21\x43",36)    #?
    # # response=send_packet(b"\x02\x21\x44",30)    # 7f Error response
    # response=send_packet(b"\x02\x21\x45",6)    #?
    # response=send_packet(b"\x02\x21\x46",8)    #?
    # #response=send_packet(b"\x02\x21\x47",30)    # 7f Error response
    # #response=send_packet(b"\x02\x21\x48",30)    # 7f Error response
    
       
    # time.sleep(0.5)


ser.close()

