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
interframe_delay=0.01
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
    ser = serial.Serial(serial_port, 300, timeout=0.1)  #CP210x is configured for 300 being 360
    command=b"\x00"
    ser.write(command) #Send a 25ms pulse
    time.sleep(0.05)
    ser.close()

def send_packet(data,res_size):
    global debug
    time.sleep(interframe_delay)

    lendata=len(data)

    modulo = sum(ord(data[i]) for i in range(lendata))
    modulo %= 256

    to_send=data+chr(modulo)
    ser.write(to_send)
    time.sleep(interframe_delay)

    ignore=len(to_send)
    read_val = ser.read(len(to_send)+res_size)

    read_val_s = read_val[0:ignore]
    if debug > 2:    
        print("Data Sent: %s." % ":".join("{:02x}".format(ord(c)) for c in read_val_s))
    read_val_r = read_val[ignore:]
    if debug > 2: 
        print("Data Received: %s." % ":".join("{:02x}".format(ord(c)) for c in read_val_r))

    modulo=0
    for i in range(len(read_val_r)-1):
        modulo += ord(read_val_r[i])
    modulo %= 256

    if (len(read_val_r) > 2) and (
        modulo != ord(read_val_r[len(read_val_r) - 1])
    ): #Checksum error
        read_val_r=""
        if debug > 1:
            print("Checksum ERROR")

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
        print("\tSeed is: %s." % ":".join("{:02x}".format(ord(c)) for c in seed))

    seed_int=ord(seed[0])*256+ord(seed[1])
    if debug > 1:
        print("\tSeed integer: %s." % seed_int)

    seed=seed_int

    count = ((seed >> 0xC & 0x8) + (seed >> 0x5 & 0x4) + (seed >> 0x3 & 0x2) + (seed & 0x1)) + 1

    for _ in range(count):
        tap = ((seed >> 1) ^ (seed >> 2 ) ^ (seed >> 8 ) ^ (seed >> 9)) & 1
        tmp = (seed >> 1) | ( tap << 0xF)
        if (seed >> 0x3 & 1) and (seed >> 0xD & 1):
                seed = tmp & ~1
        else:
                seed = tmp | 1

    if (seed<256):
        high=0x00
        low=seed
    else:
        high=seed/256
        low=seed%256

    key=chr(high)+chr(low)
    if debug > 1:
        print("\tKey hex: %s." % ":".join("{:02x}".format(ord(c)) for c in key))

    return b"\x04\x27\x02"+key

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

print("""
      \t\t Land Rover Td5 Storm - Dignostic tool
      
      Initializing..."
      
      """)

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

time.sleep(2)

#Start requesting data
while True:

    
    os.system("cls")
    print(
        f'\x1f    \t\t Td5 Storm"\x1f    Bateria Tentsioa: {b_voltage} Volt"\x1f    RPM: {rpm}\x1f    RPM Error: {rpm_error}\x1f    Abiadura: {speed} KMH"\x1f    Uraren tenperatura: {t_coolant} C"\x1f    Airearen tenperatura: {t_air} C"\x1f    Kanpoko tenperatura: {t_ext} C"\x1f    Gasoilaren tenperatura: {t_fuel} C"\x1f    Azeleragailuen pistak (Volt):{p1} {p2} {p3} {p4} {supply}\x1f    Kolektoreko presioa: {aap} Bar"\x1f    Aire Masa neurgailua: {maf}\x1f    Kanpoko presioa: {ap1} Bar"\x1f    Turboaren presioa (kalkulatua): {aap - ap1} Bar"\x1f    Zilindroak: {pb1} {pb2} {pb3} {pb4} {pb5}\x1f    EGR Modulation: N/A"\x1f    EGR Inlet: N/A"\x1f    Wastegate MOdulation: N/A'
    )


    b_voltage=get_bvolt()
    rpm=get_rpm()
    rpm_error=get_rpm_error()
    speed=get_speed()
    t_coolant, t_air, t_ext, t_fuel =get_temps()
    p1, p2, p3, p4, supply = get_throttle()
    aap, maf = get_aap_maf()
    ap1, ap2 = get_pressures()
    pb1,pb2,pb3,pb4,pb5=get_power_balance()
    
    # time.sleep(0.5)


ser.close()

