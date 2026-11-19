import machine
import time
from machine import Pin, I2C
i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=400000)
print(i2c.scan())
ID = i2c.readfrom_mem(119, 0xD0, 1, addrsize=8)
print(hex(ID[0]))
i2c.writeto_mem(119,0xF4,bytes([0x21]),addrsize=8)
time.sleep_ms(10)
Temp = list(i2c.readfrom_mem(119, 0xFA, 3, addrsize=8))
print(Temp)
print(Temp[0]<<12|Temp[1]<<4|Temp[2]>>4)
adc_T = Temp[0] << 12 | Temp[1] << 4 | Temp[2] >> 4
Temp_Cal = list(i2c.readfrom_mem(119, 0x88, 6, addrsize=8))
print(Temp_Cal)
dig_T1 = Temp_Cal[1]<<8|Temp_Cal[0]
dig_T2 = Temp_Cal[3]<<8|Temp_Cal[2]
dig_T3 = Temp_Cal[5]<<8|Temp_Cal[4]
print(dig_T1,dig_T2,dig_T3)
var_1 = (adc_T / 16384.0 - dig_T1 / 1024.0) * dig_T2
var_2 = (adc_T/131072.0 - dig_T1/8192.0) * (adc_T/131072.0 - dig_T1/8192.0) * dig_T3
t_fine = int(var_1 + var_2)
T = (var_1 + var_2)/5120.0
print(T)