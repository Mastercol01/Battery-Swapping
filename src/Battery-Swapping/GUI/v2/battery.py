#%%     IMPORTATION O0F LIBRARIES

from collections import deque
from auxiliary_funcs import bitRead
from typing import Dict, Deque, Union, Tuple




#%%     DEFINITION OF CONSTANTS


BATTERY_VARS_BY_ACTIVITY_CODE = {}
BATTERY_VARS_BY_ACTIVITY_CODE[1] =\
[
    "Total battery pack voltage",
    "Battery pack current",
    "SOC",
    "cell overvoltage warning",
    "cell overvoltage protection",
    "cell undervoltage warning",
    "cell undervoltage protection",
    "Pack voltage overvoltage warning",
    "Pack voltage overvoltage protection",
    "Pack Undervoltage warning",
    "Pack Undervoltage protection",
    "Charging high temperature warning",
    "Charging high temperature protection",
    "Charging low temperature warning",
    "Charging low temperature protection",
    "Discharge high temperature warning",
    "Discharge high temperature protection",
    "Discharge low temperature warning",
    "Discharge low temperature protection",
    "Charging overcurrent warning",
    "Charging overcurrent protection",
    "Discharge overcurrent warning",
    "Discharge overcurrent protection",
    "Short circuit protection",
    "MOSFET overtemperature warning",
    "MOSFET overtemperature protection",
    "Excessive differential pressure warning"
]

BATTERY_VARS_BY_ACTIVITY_CODE[2] =\
[
    "Excessive differential pressure protection",
    "Excessive temperature difference warning",
    "Excessive temperature difference protection",
    "SOC low alarm",
    "Acquisition chip failure",
    "Charging switch status",
    "Discharge switch status",
    "State of charge"
]

for activity_code in range(3,10):
    battery_num = int( 4*(activity_code-3) + 1 )
    BATTERY_VARS_BY_ACTIVITY_CODE[activity_code] = [f"cell {battery_num + i} voltage" for i in range(4)] 


BATTERY_VARS_BY_ACTIVITY_CODE[10] =\
[
    "cell 29 voltage",
    "cell 30 voltage",
    "NTC1 temperature value",
    "NTC2 temperature value",
    "NTC3 temperature value",
    "NTC4 temperature value"
]

BATTERY_VARS_BY_ACTIVITY_CODE[11] =\
[
    "NTC5 temperature value",
    "NTC6 temperature value",
    "MOSFET temperature value"
]

BATTERY_VARS = set()
for val in BATTERY_VARS_BY_ACTIVITY_CODE.values():
    BATTERY_VARS = BATTERY_VARS.union(set(val))

BATTERY_VARS_BY_CATEGORY = {}
BATTERY_VARS_BY_CATEGORY["General Status"] =\
[
    "Total battery pack voltage",
    "Battery pack current",
    "SOC"
]
BATTERY_VARS_BY_CATEGORY["Warnings"] =\
[
    "cell overvoltage warning",
    "cell overvoltage protection",
    "cell undervoltage warning",
    "cell undervoltage protection",
    "Pack voltage overvoltage warning",
    "Pack voltage overvoltage protection",
    "Pack Undervoltage warning",
    "Pack Undervoltage protection",
    "Charging high temperature warning",
    "Charging high temperature protection",
    "Charging low temperature warning",
    "Charging low temperature protection",
    "Discharge high temperature warning",
    "Discharge high temperature protection",
    "Discharge low temperature warning",
    "Discharge low temperature protection",
    "Charging overcurrent warning",
    "Charging overcurrent protection",
    "Discharge overcurrent warning",
    "Discharge overcurrent protection",
    "Short circuit protection",
    "MOSFET overtemperature warning",
    "MOSFET overtemperature protection",
    "Excessive differential pressure warning"
    "Excessive differential pressure protection",
    "Excessive temperature difference warning",
    "Excessive temperature difference protection",
    "SOC low alarm",
    "Acquisition chip failure",
    "Charging switch status",
    "Discharge switch status",
    "State of charge"
]
BATTERY_VARS_BY_CATEGORY["Cell Voltages"] = [f"cell {i} voltage" for i in range(1,31)]
BATTERY_VARS_BY_CATEGORY["Temperatures"]  = [f"NTC{i} temperature value" for i in range(1, 7)]
BATTERY_VARS_BY_CATEGORY["Temperatures"].append("MOSFET temperature value")

ACTIVITY_CODE_OF_BATTERY_VARS = {}
for key,val in BATTERY_VARS_BY_ACTIVITY_CODE.items():
    for var in val:
        ACTIVITY_CODE_OF_BATTERY_VARS[var] = key

CATEGORY_OF_BATTERY_VARS = {}
for key,val in BATTERY_VARS_BY_CATEGORY.items():
    for var in val:
        CATEGORY_OF_BATTERY_VARS[var] = key
        



#%%     DEFINITION OF AUXILIARY FUNCTIONS


def pack_voltage_from_bytes(byte_0 : int, byte_1 : int) -> float:
    """
    Get pack voltage from canMsg bytes.

    Parameters
    ----------
    byte_0 : int
        Least signifcant byte. Must be a number from 0 to 255.

    byte_1 : int
        Most signifcant byte. Must be a number from 0 to 255.

    Returns
    -------
    res : float
        Battery pack voltage [V].

    Notes
    -----
    The significance of bytes is determined according to 'little endian' ordering.
    """

    combined_bytes = (byte_1 << 8) | byte_0
    pack_voltage = 0.1*combined_bytes
    return pack_voltage


def pack_current_from_bytes(byte_0 : int, byte_1 : int) -> float:
    """
    Get pack current from canMsg bytes.

    Parameters
    ----------
    byte_0 : int
        Least signifcant byte. Must be a number from 0 to 255.

    byte_1 : int
        Most signifcant byte. Must be a number from 0 to 255.

    Returns
    -------
    res : float
        Battery pack current [A].

    Notes
    -----
    The significance of bytes is determined according to 'little endian' ordering.
    """
    combined_bytes = (byte_1 << 8) | byte_0
    pack_current = 0.1*(combined_bytes - 32000)
    return pack_current


def cell_voltage_from_bytes(byte_0 : int, byte_1 : int) -> float:
    """
    Get cell voltage from canMsg bytes.

    Parameters
    ----------
    byte_0 : int
        Least signifcant byte. Must be a number from 0 to 255.

    byte_1 : int
        Most signifcant byte. Must be a number from 0 to 255.

    Returns
    -------
    res : float
        Cell voltage [V].

    Notes
    -----
    The significance of bytes is determined according to 'little endian' ordering.
    """
    combined_bytes = (byte_1 << 8) | byte_0
    cell_voltage = 0.001*combined_bytes
    return cell_voltage


def NTC_temperature_from_byte(byte : int) -> int:
    """
    Get temperature of NTC thermistor inside the battery from a canMsg byte.

    Parameters
    ----------
    byte: int
        canMsg byte.

    Returns
    -------
    res : float
        NTC thermistor temperature [Celsius].

    """
    return byte - 40




#%%                  DEFINITION OF MAIN FUNCTIONS


def get_battery_data_from_canMsg_attributes_when_activity_code_is_1(canMsg_timestamp : float, canMsg_data : bytearray) -> Dict[str, Union[int, float]]:

    """
    Get battery data from canMsg attributes when its activity code is 1.

    Parameters
    ----------
    canMsg_timestamp : float
        Timestamp of canMsg obj. It is number representing when the message was received since the epoch in seconds. In raspberry Pi and other unix systems
        the 'epoch' is set to January 1st, 1970 at 12:00:00 AM, Greenwhich Mean Time (GMT-00:00)

    canMsg_data : bytearray
        Data of canMsg obj. Must be a bytearray of length 8.

    Returns
    -------
    res : dict of {str : int, float}
        Miscellaneous battery data. The specific descriptions of the data retrieved are those found in BATTERY_VARS_BY_ACTIVITY_CODE[1].
    """

    res = {}
    res["timestamp"]                               = canMsg_timestamp 
    res["Total battery pack voltage"]              = pack_voltage_from_bytes(canMsg_data[0], canMsg_data[1])
    res["Battery pack current"]                    = pack_current_from_bytes(canMsg_data[2], canMsg_data[3])
    res["SOC"]                                     = canMsg_data[4]
    res["cell overvoltage warning"]                = bitRead(canMsg_data[5], 0)
    res["cell overvoltage protection"]             = bitRead(canMsg_data[5], 1)
    res["cell undervoltage warning"]               = bitRead(canMsg_data[5], 2)
    res["cell undervoltage protection"]            = bitRead(canMsg_data[5], 3)
    res["Pack voltage overvoltage warning"]        = bitRead(canMsg_data[5], 4)
    res["Pack voltage overvoltage protection"]     = bitRead(canMsg_data[5], 5)
    res["Pack Undervoltage warning"]               = bitRead(canMsg_data[5], 6)
    res["Pack Undervoltage protection"]            = bitRead(canMsg_data[5], 7)
    res["Charging high temperature warning"]       = bitRead(canMsg_data[6], 0)
    res["Charging high temperature protection"]    = bitRead(canMsg_data[6], 1)
    res["Charging low temperature warning"]        = bitRead(canMsg_data[6], 2)
    res["Charging low temperature protection"]     = bitRead(canMsg_data[6], 3)
    res["Discharge high temperature warning"]      = bitRead(canMsg_data[6], 4)
    res["Discharge high temperature protection"]   = bitRead(canMsg_data[6], 5)
    res["Discharge low temperature warning"]       = bitRead(canMsg_data[6], 6)
    res["Discharge low temperature protection"]    = bitRead(canMsg_data[6], 7)
    res["Charging overcurrent warning"]            = bitRead(canMsg_data[7], 0)
    res["Charging overcurrent protection"]         = bitRead(canMsg_data[7], 1)
    res["Discharge overcurrent warning"]           = bitRead(canMsg_data[7], 2)
    res["Discharge overcurrent protection"]        = bitRead(canMsg_data[7], 3)
    res["Short circuit protection"]                = bitRead(canMsg_data[7], 4)
    res["MOSFET overtemperature warning"]          = bitRead(canMsg_data[7], 5)
    res["MOSFET overtemperature protection"]       = bitRead(canMsg_data[7], 6)
    res["Excessive differential pressure warning"] = bitRead(canMsg_data[7], 7)

    return res


def get_battery_data_from_canMsg_attributes_when_activity_code_is_2(canMsg_timestamp : float, canMsg_data : bytearray) -> Dict[str, Union[int, float]]:

    """
    Get battery data from canMsg attributes when its activity code is 2.

    Parameters
    ----------
    canMsg_timestamp : float
        Timestamp of canMsg obj. It is number representing when the message was received since the epoch in seconds. In raspberry Pi and other unix systems
        the 'epoch' is set to January 1st, 1970 at 12:00:00 AM, Greenwhich Mean Time (GMT-00:00)

    canMsg_data : bytearray
        Data of canMsg obj. Must be a bytearray of length 8.

    Returns
    -------
    res : dict of {str : int, float}
        Miscellaneous battery data. The specific descriptions of the data retrieved are those found in BATTERY_VARS_BY_ACTIVITY_CODE[2].
    """

    res = {}
    res["timestamp"]                                   = canMsg_timestamp 
    res["Excessive differential pressure protection"]  = bitRead(canMsg_data[0], 0)
    res["Excessive temperature difference warning"]    = bitRead(canMsg_data[0], 1)
    res["Excessive temperature difference protection"] = bitRead(canMsg_data[0], 2)
    res["SOC low alarm"]                               = bitRead(canMsg_data[0], 3)
    res["Acquisition chip failure"]                    = bitRead(canMsg_data[0], 4)
    res["Charging switch status"]                      = bitRead(canMsg_data[1], 0)
    res["Discharge switch status"]                     = bitRead(canMsg_data[1], 1)
    res["State of charge"]                             = bitRead(canMsg_data[1], 2)

    return res


def get_battery_data_from_canMsg_attributes_when_activity_code_is_between_3_and_9(canMsg_activity_code : int, canMsg_timestamp : float, canMsg_data : bytearray) -> Dict[str, Union[int, float]]:

    """
    Get battery data from canMsg attributes when its activity code is between 3 and 9 (inclusive).

    Parameters
    ----------
    canMsg_activity_code : int
        Activity code of canMsg obj. Must be a number between 3 and 9 (inclusive).

    canMsg_timestamp : float
        Timestamp of canMsg obj. It is number representing when the message was received since the epoch in seconds. In raspberry Pi and other unix systems
        the 'epoch' is set to January 1st, 1970 at 12:00:00 AM, Greenwhich Mean Time (GMT-00:00)

    canMsg_data : bytearray
        Data of canMsg obj. Must be a bytearray of length 8.

    Returns
    -------
    res : dict of {str : int, float}
        Miscellaneous battery data. The specific descriptions of the data retrieved are those found from BATTERY_VARS_BY_ACTIVITY_CODE[3]
        to BATTERY_VARS_BY_ACTIVITY_CODE[9].
    """

    res = {}
    cell_num= int( 4*(canMsg_activity_code-3) + 1 )

    res["timestamp"]                    = canMsg_timestamp 
    res[f"cell {cell_num} voltage"]     = cell_voltage_from_bytes(canMsg_data[0], canMsg_data[1])
    res[f"cell {cell_num + 1} voltage"] = cell_voltage_from_bytes(canMsg_data[2], canMsg_data[3])
    res[f"cell {cell_num + 2} voltage"] = cell_voltage_from_bytes(canMsg_data[4], canMsg_data[5])
    res[f"cell {cell_num + 3} voltage"] = cell_voltage_from_bytes(canMsg_data[6], canMsg_data[7])

    return res


def get_battery_data_from_canMsg_attributes_when_activity_code_is_10(canMsg_timestamp : float, canMsg_data : bytearray) -> Dict[str, Union[int, float]]:

    """
    Get battery data from canMsg attributes when its activity code is 10.

    Parameters
    ----------
    canMsg_timestamp : float
        Timestamp of canMsg obj. It is number representing when the message was received since the epoch in seconds. In raspberry Pi and other unix systems
        the 'epoch' is set to January 1st, 1970 at 12:00:00 AM, Greenwhich Mean Time (GMT-00:00)

    canMsg_data : bytearray
        Data of canMsg obj. Must be a bytearray of length 8.

    Returns
    -------
    res : dict of {str : int, float}
        Miscellaneous battery data. The specific descriptions of the data retrieved are those found in BATTERY_VARS_BY_ACTIVITY_CODE[10].
    """

    res = {}
    res["timestamp"]              = canMsg_timestamp 
    res["cell 29 voltage"]        = cell_voltage_from_bytes(canMsg_data[0], canMsg_data[1])
    res["cell 30 voltage"]        = cell_voltage_from_bytes(canMsg_data[2], canMsg_data[3])
    res["NTC1 temperature value"] = NTC_temperature_from_byte(canMsg_data[4])
    res["NTC2 temperature value"] = NTC_temperature_from_byte(canMsg_data[5])
    res["NTC3 temperature value"] = NTC_temperature_from_byte(canMsg_data[6])
    res["NTC4 temperature value"] = NTC_temperature_from_byte(canMsg_data[7])

    return res


def get_battery_data_from_canMsg_attributes_when_activity_code_is_11(canMsg_timestamp : float, canMsg_data : bytearray) -> Dict[str, Union[int, float]]:

    """
    Get battery data from canMsg attributes when its activity code is 11.

    Parameters
    ----------
    canMsg_timestamp : float
        Timestamp of canMsg obj. It is number representing when the message was received since the epoch in seconds. In raspberry Pi and other unix systems
        the 'epoch' is set to January 1st, 1970 at 12:00:00 AM, Greenwhich Mean Time (GMT-00:00)

    canMsg_data : bytearray
        Data of canMsg obj. Must be a bytearray of length 8.

    Returns
    -------
    res : dict of {str : int, float}
        Miscellaneous battery data. The specific descriptions of the data retrieved are those found in BATTERY_VARS_BY_ACTIVITY_CODE[11].
    """

    res = {}
    res["timestamp"]                = canMsg_timestamp 
    res["NTC5 temperature value"]   = NTC_temperature_from_byte(canMsg_data[0])
    res["NTC6 temperature value"]   = NTC_temperature_from_byte(canMsg_data[1])
    res["MOSFET temperature value"] = NTC_temperature_from_byte(canMsg_data[2])

    return res


def get_battery_data_from_canMsg_attributes_when_activity_code_is_between_1_and_11(canMsg_activity_code : int, canMsg_timestamp : float, canMsg_data : bytearray) -> Dict[str, Union[int, float]]:

    """
    Get battery data from canMsg attributes when its activity code is between 1 and 11 (inclusive).

    Parameters
    ----------
    canMsg_activity_code : int
        Activity code of canMsg obj. Must be a number between 1 and 11 (inclusive).

    canMsg_timestamp : float
        Timestamp of canMsg obj. It is number representing when the message was received since the epoch in seconds. In raspberry Pi and other unix systems
        the 'epoch' is set to January 1st, 1970 at 12:00:00 AM, Greenwhich Mean Time (GMT-00:00)

    canMsg_data : bytearray
        Data of canMsg obj. Must be a bytearray of length 8.

    Returns
    -------
    res : dict of {str : int, float}
        Miscellaneous battery data. The specific descriptions of the data retrieved are those found from BATTERY_VARS_BY_ACTIVITY_CODE[1]
        to BATTERY_VARS_BY_ACTIVITY_CODE[11].

    Raises
    ------
    1) Exception:
            "Activity code must be an integer between 1 and 11 (inclusive)."

    """

    if canMsg_activity_code == 1:
        res = get_battery_data_from_canMsg_attributes_when_activity_code_is_1(canMsg_timestamp, canMsg_data)

    elif canMsg_activity_code == 2:
        res = get_battery_data_from_canMsg_attributes_when_activity_code_is_2(canMsg_timestamp, canMsg_data)

    elif 3 <= canMsg_activity_code <= 9:
        res = get_battery_data_from_canMsg_attributes_when_activity_code_is_between_3_and_9(canMsg_activity_code, canMsg_timestamp, canMsg_data)

    elif canMsg_activity_code == 10:
        res = get_battery_data_from_canMsg_attributes_when_activity_code_is_10(canMsg_timestamp, canMsg_data)

    elif canMsg_activity_code == 11:
        res = get_battery_data_from_canMsg_attributes_when_activity_code_is_11(canMsg_timestamp, canMsg_data)

    else:
        raise Exception("Activity code must be an integer between 1 and 11 (inclusive).")
    
    return res




#%%           DEFINITION OF CLASSES 


class Battery:
    def __init__(self, address : int, num_pts : int):

        self.num_pts = num_pts
        self.address = address
        self.variables = {var:deque(maxlen=num_pts) for var in BATTERY_VARS}
        self.times = {activity_code:deque(maxlen=num_pts) for activity_code in range(1,12)}

        self.BATTERY_VARS = BATTERY_VARS
        self.BATTERY_VARS_BY_CATEGORY = BATTERY_VARS_BY_CATEGORY
        self.CATEGORY_OF_BATTERY_VARS = CATEGORY_OF_BATTERY_VARS
        self.BATTERY_VARS_BY_ACTIVITY_CODE = BATTERY_VARS_BY_ACTIVITY_CODE
        self.ACTIVITY_CODE_OF_BATTERY_VARS = ACTIVITY_CODE_OF_BATTERY_VARS

        return None
    
    def update_variables_from_canMsg_attributes(self, canMsg_activity_code : int, canMsg_timestamp : float, canMsg_data : bytearray) -> None:

        """
        Update battery variables from canMsg attributes. 

        Parameters
        ----------
        canMsg_activity_code : int
            Activity code of canMsg obj. Must be a number between 1 and 11 (inclusive).

        canMsg_timestamp : float
            Timestamp of canMsg obj. It is number representing when the message was received since the epoch in seconds. In raspberry Pi and other unix systems
            the 'epoch' is set to January 1st, 1970 at 12:00:00 AM, Greenwhich Mean Time (GMT-00:00)

        canMsg_data : bytearray
            Data of canMsg obj. Must be a bytearray of length 8.

        Returns
        -------
        res : dict of {str : int, float}
            Miscellaneous battery data. The specific descriptions of the data retrieved are those found from BATTERY_VARS_BY_ACTIVITY_CODE[1]
            to BATTERY_VARS_BY_ACTIVITY_CODE[11].

        """

        battery_data = get_battery_data_from_canMsg_attributes_when_activity_code_is_between_1_and_11(canMsg_activity_code, canMsg_timestamp, canMsg_data)
        self.times[canMsg_activity_code].append(battery_data["timestamp"])
        del battery_data["timestamp"]

        for key, val in battery_data.items():
            self.variables[key].append(val)

        return None

    
    def get_var_and_time(self, var_name : str) -> Tuple[Deque, Deque]:
        var = self.variables[var_name]
        time = self.times[self.ACTIVITY_CODE_OF_BATTERY_VARS[var_name]]
        return var, time




#%%        TESTING

if __name__ == "__main__":
    bat = Battery(1, num_pts=200)
    print(bat.get_var_and_time("SOC"))

