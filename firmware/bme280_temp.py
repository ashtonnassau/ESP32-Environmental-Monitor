# BME280 temperature reader (MicroPython, ESP32)
# Wiring: SDA to GPIO21, SCL to GPIO22, 3V3 and GND to the power rails
# Reads the sensor's registers directly over I2C (no driver library) and converts the raw reading to degrees
# C using the formulas in the Bosch datasheet for the BME280.
import machine
import time
from machine import Pin, I2C
# I2C bus 1 on the pins wired to the sensor; 400 kHz is I2C "fast mode"
i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=400000)
ID = i2c.readfrom_mem(119, 0xD0, 1, addrsize=8)
if ID[0] != 0x60:
    raise RuntimeError("BME280 not found")
Temp_Cal = list(i2c.readfrom_mem(119, 0x88, 6, addrsize=8))
dig_T1 = Temp_Cal[1]<<8|Temp_Cal[0]
dig_T2 = Temp_Cal[3]<<8|Temp_Cal[2]
if dig_T2 >= 32768:
    dig_T2 -= 65536
dig_T3 = Temp_Cal[5]<<8|Temp_Cal[4]
if dig_T3 >= 32768:
    dig_T3 -= 65536
try:
    while True:
        i2c.writeto_mem(119,0xF4,bytes([0x21]),addrsize=8)
        time.sleep_ms(10)
        Temp = list(i2c.readfrom_mem(119, 0xFA, 3, addrsize=8))
        adc_T = Temp[0] << 12 | Temp[1] << 4 | Temp[2] >> 4
        var_1 = (adc_T / 16384.0 - dig_T1 / 1024.0) * dig_T2
        var_2 = (adc_T/131072.0 - dig_T1/8192.0) * (adc_T/131072.0 - dig_T1/8192.0) * dig_T3
        t_fine = int(var_1 + var_2)
        T = (var_1 + var_2)/5120.0
        print(f"{T:.2f}")
        time.sleep(2)
except KeyboardInterrupt:
    pass