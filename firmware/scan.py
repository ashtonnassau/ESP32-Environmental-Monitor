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
Temp_Cal = list(i2c.readfrom_mem(119, 0x88, 6, addrsize=8))
print(Temp_Cal)