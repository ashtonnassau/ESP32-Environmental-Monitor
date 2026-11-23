# BME280 temperature reader (MicroPython, ESP32)
# Wiring: SDA to GPIO21, SCL to GPIO22, 3V3 and GND to the power rails
# Reads the sensor's registers directly over I2C (no driver library) and converts the raw reading to degrees
# C using the formulas in the Bosch datasheet for the BME280.
import machine
import time
from machine import Pin, I2C
# I2C bus 1 on the pins wired to the sensor. 400 kHz is I2C fast mode
i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=400000)
# The BME280 answers at address 0x77 (119 in decimal). The I2C scan found it at this address
# Register 0xD0 is the chip ID. A BME280 always returns 0x60, so this catches a wrong sensor 
# or a wiring fault before any readings are made
ID = i2c.readfrom_mem(119, 0xD0, 1, addrsize=8)
if ID[0] != 0x60:
    raise RuntimeError("BME280 not found")

# TEMPERATURE CALIBRATION #

# Calibration constants: 6 bytes starting at register 0x88 hold dig_T1, dig_T2 and dig_T3 (2 bytes each)
Temp_Cal = list(i2c.readfrom_mem(119, 0x88, 6, addrsize=8))
# The chip stores each 16-bit value low byte first, so the second byte is the high one
dig_T1 = Temp_Cal[1]<<8|Temp_Cal[0]
# dig_T2 and dig_T3 are signed. A 16-bit number runs 0 to 65535, and values from
# 32768 up stand for negatives, so subtract 65536 (dig_T1 is unsigned, no fix)
dig_T2 = Temp_Cal[3]<<8|Temp_Cal[2]
if dig_T2 >= 32768:
    dig_T2 -= 65536
dig_T3 = Temp_Cal[5]<<8|Temp_Cal[4]
if dig_T3 >= 32768:
    dig_T3 -= 65536

# PRESSURE CALIBRATION #

# Calibration constants: 6 bytes starting at register 0x8E hold dig_P1 to dig_P9 (2 bytes each)
Press_Cal = list(i2c.readfrom_mem(119, 0x8E, 18, addrsize = 8))
# The chip stores each 16-bit value low byte first, so the second byte is the high one
dig_P1 = Press_Cal[1]<<8|Press_Cal[0]
# dig_P2 to dig_P9 are signed. A 16-bit number runs 0 to 65535, and values from
# 32768 up stand for negatives, so subtract 65536 (dig_P1 is unsigned, no fix)
dig_P2 = Press_Cal[3]<<8|Press_Cal[2]
if dig_P2 >= 32768:
    dig_P2 -= 65536
dig_P3 = Press_Cal[5]<<8|Press_Cal[4]
if dig_P3 >= 32768:
    dig_P3 -= 65536
dig_P4 = Press_Cal[7]<<8|Press_Cal[6]
if dig_P4 >= 32768:
    dig_P4 -= 65536
dig_P5 = Press_Cal[9]<<8|Press_Cal[8]
if dig_P5 >= 32768:
    dig_P5 -= 65536
dig_P6 = Press_Cal[11]<<8|Press_Cal[10]
if dig_P6 >= 32768:
    dig_P6 -= 65536
dig_P7 = Press_Cal[13]<<8|Press_Cal[12]
if dig_P7 >= 32768:
    dig_P7 -= 65536
dig_P8 = Press_Cal[15]<<8|Press_Cal[14]
if dig_P8 >= 32768:
    dig_P8 -= 65536
dig_P9 = Press_Cal[17]<<8|Press_Cal[16]
if dig_P9 >= 32768:
    dig_P9 -= 65536

try:
    while True:
        # ctrl_meas (0xF4): temperature x1 (001), pressure x1 (001), forced mode (01).
        # Forced mode measures once, then the chip goes back to sleep, so this
        # has to be sent before every reading, not once at the start
        i2c.writeto_mem(119,0xF4,bytes([0x25]),addrsize=8)
        time.sleep_ms(20)

        # TEMPERATURE CALCULATION #

        # temp_msb, temp_lsb, temp_xlsb: a 20-bit raw value spread over 3 bytes
        # (the last byte only contributes its top 4 bits)
        Temp = list(i2c.readfrom_mem(119, 0xFA, 3, addrsize=8))
        adc_T = Temp[0] << 12 | Temp[1] << 4 | Temp[2] >> 4
        # Compensation formula from the Bosch datasheet (floating-point version)
        var_1 = (adc_T / 16384.0 - dig_T1 / 1024.0) * dig_T2
        var_2 = (adc_T/131072.0 - dig_T1/8192.0) * (adc_T/131072.0 - dig_T1/8192.0) * dig_T3
        t_fine = int(var_1 + var_2)
        T = (var_1 + var_2)/5120.0

        # PRESSURE CALCULATION #

        # press_msb, press_lsb, press_xlsb: a 20-bit raw value spread over 3 bytes
        # (the last byte only contributes its top 4 bits)
        Pressure = list (i2c.readfrom_mem(119, 0xF7, 3, addrsize = 8))
        adc_P = Pressure[0] << 12 | Pressure[1] << 4 | Pressure[2] >> 4
        # Compensation formula from the Bosch datasheet (floating-point version)
        p_var_1 = t_fine/2.0 - 64000
        p_var_2 = p_var_1 * p_var_1 * dig_P6/32768.0
        p_var_2 = p_var_2 + p_var_1 * dig_P5 * 2.0
        p_var_2 = p_var_2/4.0 + dig_P4 * 65536.0
        p_var_1 = (dig_P3 * p_var_1 * p_var_1/524288.0 + dig_P2 * p_var_1)/524288.0
        p_var_1 = (1.0 + p_var_1/32768.0) * dig_P1
        # Prevents error due to zero division
        if p_var_1 == 0.0:
            P = 0
        else:
            p = 1048576.0 - adc_P
            p = (p - p_var_2/4096.0) * 6250.0/p_var_1
            p_var_1 = dig_P9 * p * p/2147483648.0
            p_var_2 = p * dig_P8/32768.0
            P = p + (p_var_1 + p_var_2 + dig_P7)/16.0

        # Displays temperature and pressure readings every 2 seconds
        print(f"Temperature: {T:.2f}")
        print(f"Pressure: {P/100:.2f} hPa")
        time.sleep(2)
except KeyboardInterrupt:
    # Ctrl+C ends the loop quietly
    pass