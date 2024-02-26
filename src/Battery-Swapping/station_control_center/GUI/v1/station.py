from collections import deque

BATTERY_STATUS_KEYS_DESCRIPTION = \
{
    "pack_voltage" : "Total battery pack voltage",
    "pack_current" : "Battery pack current",
    "SOC" : "State of Charge"
}

BATTERY_WARNINGS_AND_PROTECTIONS_KEYS_DESCRIPTION = \
{
    "cell overvoltage warning"                     : "cell overvoltage warning",
    "cell_overvoltage_protection"                  : "cell overvoltage protection",
    "cell_undervoltage_warning"                    : "cell undervoltage warning",
    "cell_undervoltage_protection"                 : "cell undervoltage protection",
    "Pack voltage overvoltage warning"             : "Pack voltage overvoltage warning",
    "Pack voltage overvoltage protection"          : "Pack voltage overvoltage protection",
    "Pack Undervoltage warning"                    : "Pack Undervoltage warning",   
    "Pack Undervoltage protection"                 : "Pack Undervoltage protection",
    "Charging high temperature warning"            : "Charging high temperature warning",
    "Charging high temperature protection"         : "Charging high temperature protection",
    "Charging low temperature warning"             : "Charging low temperature warning",
    "Charging low temperature protection"          : "Charging low temperature protection",
    "Discharge high temperature warning"           : "Discharge high temperature warning",
    "Discharge high temperature protection"        : "Discharge high temperature protection",
    "Discharge low temperature warning"            : "Discharge low temperature warning",
    "Discharge low temperature protection"         : "Discharge low temperature protection",
    "Charging overcurrent warning"                 : "Charging overcurrent warning",
    "Charging overcurrent protection"              : "Charging overcurrent protection",
    "Discharge overcurrent warning"                : "Discharge overcurrent warning",
    "Discharge overcurrent protection"             : "Discharge overcurrent protection",
    "Short circuit protection"                     : "Short circuit protection",
    "MOSFET overtemperature warning"               : "MOSFET overtemperature warning",
    "MOSFET overtemperature protection"            : "MOSFET overtemperature protection",
    "Excessive differential pressure warning"      : "Excessive differential pressure warning",
    "Excessive differential pressure protection"   : "Excessive differential pressure protection", 
    "Excessive temperature difference warning"     : "Excessive temperature difference warning",
    "Excessive temperature difference protection"  : "Excessive temperature difference protection",
    "SOC low alarm"                                : "SOC low alarm",
    "Acquisition chip failure"                     : "Acquisition chip failure",
    "Charging switch status"                       : "Charging switch status",
    "Discharge switch status"                      : "Discharge switch status"
}

BATTERY_CELL_VOLTAGES = {f"V{i}" : "cell {i} voltage" for i in range(1,31)}

BATTERY_TEMPERATURES = {f"T{i}" : "NTC{i} temperature value" for i in range(1,5)}



def read_bit_from_byte(x, n):
    str_x = bin(256|x)[3:]
    return int(str_x[n])


class Battery:
    def __init__(self, num_saved_pts = 200):

        self.pack_data = {}
        for key in BATTERY_STATUS_KEYS_DESCRIPTION.keys():
            self.pack_data[key] = deque(maxlen=num_saved_pts)

        self.pack_warnings_and_protections = {}
        for key in BATTERY_WARNINGS_AND_PROTECTIONS_KEYS_DESCRIPTION.keys():
            self.pack_warnings_and_protections[key] = deque(maxlen=num_saved_pts)

        self.cell_voltages = {}
        for key in BATTERY_CELL_VOLTAGES.keys():
            self.cell_voltages[key] = deque(maxlen=num_saved_pts)

        self.temperatures = {}
        for key in BATTERY_TEMPERATURES.keys():
            self.temperatures[key] = deque(maxlen=num_saved_pts)
        
        return None
    
    @staticmethod
    def pack_voltage_from_bytes(byte_0, byte_1):
        combined_bytes = (byte_1 << 8) | byte_0
        pack_voltage = 0.1*combined_bytes
        return pack_voltage
    
    @staticmethod
    def pack_current_from_bytes(byte_0, byte_1):
        combined_bytes = (byte_1 << 8) | byte_0
        pack_current = 0.1*(combined_bytes - 32000)
        return pack_current
    
    @staticmethod
    def cell_voltage_from_byte(byte):
        return 0.001*byte
    
    @staticmethod
    def NTC_temperature_from_byte(byte):
        return byte - 40
    


class Module:
    def __init__(self, id):
        pass