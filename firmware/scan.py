import machine
from machine import Pin, I2C
i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=400000)
print(i2c.scan())
ID = i2c.readfrom_mem(119, 0xD0, 1, addrsize=8)
print(hex(ID[0]))