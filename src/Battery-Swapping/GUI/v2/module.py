
#%%     IMPORTATION OF LIBRARIES

from typing import Union
from battery import Battery
from collections import deque
from can import Bus, Message, CanError
from auxiliary_funcs import create_canMsg_canId, get_activity_code_from_canMsg_canId, get_origin_address_from_canMsg_canId




#%%     DEFINITION OF CONSTANTS

CONTROL_CENTER_ADDRESS = 9




#%%     DEFINITION OF CLASSES


class Module:
    def __init__(self, address : int, num_pts : int, canBus : Bus, bms_connection_to_relay_is_normally_open : bool = True):
        
        self.canBus  = canBus
        self.address = address
        self.num_pts = num_pts
        self.battery = Battery(address=address, num_pts=num_pts)
        self.MAX_NUM_ATTEMPTS_TO_SEND_canMsg = 5

        self.states =\
        {
            "relay"                  : deque(maxlen=num_pts),
            "door_lock_solenoid"     : deque(maxlen=num_pts),
            "battery_lock_solenoid"  : deque(maxlen=num_pts),
            "reed_switch"            : deque(maxlen=num_pts),
            "led_strip"              : deque(maxlen=num_pts),
            "bms_connection"         : deque(maxlen=num_pts),
            "bms_connection_error"   : deque(maxlen=num_pts),
            "extra_priority_level"   : deque(maxlen=num_pts)
        }
        self.times = deque(maxlen=num_pts) 


        self.default_byCommand_priorities =\
        {
            1 : 4,
            2 : 6,
            3 : 6,
            4 : 6,
            5 : 5,
            6 : 4,
            7 : 4
        }

        self.timeouts =\
        {
            "send_module_states" : 0,
            "send_battery_data"  : 0,
            "bms_connection"     : 0
        }

        
        self.bms_connection_to_relay_is_normally_open =\
        bms_connection_to_relay_is_normally_open

        return None
    

    def send_canMsg(self, canMsg : Message) -> None:

        """
        Send canMsg over the can Bus.

        Parameters
        ----------
        canMsg : Message obj
            canMsg to send.

        Returns
        -------
        None

        """

        num_attempts = 0 
        while num_attempts < self.MAX_NUM_ATTEMPTS_TO_SEND_canMsg:

            try:
                self.canBus.send(canMsg)
                num_attempts = self.MAX_NUM_ATTEMPTS_TO_SEND_canMsg + 1
                print("Message sent")

            except CanError:
                num_attempts += 1
                print("Message not sent")

        return None
    
    
    def update_from_canMsg(self, canMsg : Message) -> None:

        """
        Update module battery data, module states and module timeouts from canMsg sent by the corresponding 'individual control module'.

        Parameters
        ----------
        canMsg : Message obj
            canMsg sent by the 'individual control module' with address = {self.address}.

        Returns
        -------
        None

        Raises
        ------
        1) Exception:
             "canMsg is not intended for this module adress!"

        2) Exception:
             "Activity code must be an integer between 1 and 13 (inclusive)."

        """

        if get_origin_address_from_canMsg_canId(canMsg.arbitration_id) != self.address:
            raise Exception("canMsg is not intended for this module adress!")
        
        activity_code = get_activity_code_from_canMsg_canId(canMsg.arbitration_id)

        if 1 <= activity_code <= 11:
            self.battery.update_variables_from_canMsg_attributes(activity_code, canMsg.timestamp, canMsg.data)

        elif activity_code == 12:
            self.__update_states_from_canMsg_attributes(canMsg.timestamp, canMsg.data)
    
        elif activity_code == 13:
            self.__update_timeouts_from_canMsg_attributes(canMsg.data)

        else:
            raise Exception("Activity code must be an integer between 1 and 13 (inclusive).")
        
        return None
    

    def __update_states_from_canMsg_attributes(self, canMsg_timestamp : float, canMsg_data : bytearray) -> None:

        """
        Update module states from canMsg attributes.

        Parameters
        ----------
        canMsg_timestamp : float
        Timestamp of canMsg obj. It is number representing when the message was received since the epoch in seconds. In raspberry Pi and other unix systems
        the 'epoch' is set to January 1st, 1970 at 12:00:00 AM, Greenwhich Mean Time (GMT-00:00)

        canMsg_data : bytearray
            Data of canMsg obj. Must be a bytearray of length 8.

        Returns
        -------
        None

        """

        self.times.append(canMsg_timestamp)
        self.states["relay"].append(canMsg_data[0])
        self.states["door_lock_solenoid"].append(canMsg_data[1])
        self.states["battery_lock_solenoid"].append(canMsg_data[2])
        self.states["reed_switch"].append(canMsg_data[3])
        self.states["led_strip"].append(canMsg_data[4])
        self.states["bms_connection"].append(canMsg_data[5])
        self.states["bms_connection_error"].append(canMsg_data[6])
        self.states["extra_priority_level"].append(canMsg_data[7])

        return None
    

    def __update_timeouts_from_canMsg_attributes(self, canMsg_data : bytearray) -> None:

        """
        Update module timeouts from canMsg attributes.

        Parameters
        ----------
        canMsg_data : bytearray
            Data of canMsg obj. Must be a bytearray of length 8.

        Returns
        -------
        None

        """

        self.timeouts["send_module_states"] = (canMsg_data[1] << 8) | canMsg_data[0]
        self.timeouts["send_battery_data"]  = (canMsg_data[3] << 8) | canMsg_data[2]
        self.timeouts["bms_connection"]     = (canMsg_data[5] << 8) | canMsg_data[4]

        return None
    

    def byCommand_set_peripherals_states(self, 
                                         relay_state                 : Union[None, int] = None, 
                                         door_lock_solenoid_state    : Union[None, int] = None, 
                                         battery_lock_solenoid_state : Union[None, int] = None,
                                         led_strip_state             : Union[None, int] = None,
                                         canMsg_priority_level       : Union[None, int] = None) -> None:
        
        
        """
        Send a canMsg obj over the canBus with information required to set the states of the peripherals 
        of the 'individual control module' with address = {self.address}.

        Parameters
        ----------
        relay_state : None or {0, 1}
            New state to which the relay is going to be set. 
            If 0, the relay will be set to turn OFF.
            If 1, the relay will be set to turn ON. 
            If None, the relay will remain unchanged. 
            Default is None.

        door_lock_solenoid_state : None or {0, 1}
            New state to which the door lock solenoid is going to be set. 
            If 0, the door lock solenoid will be set to turn OFF.
            If 1, the door lock solenoid will be set to turn ON. 
            If None, the door lock solenoid will remain unchanged. 
            Default is None.

        battery_lock_solenoid_state : None or {0, 1}
            New state to which the battery lock solenoid is going to be set. 
            If 0, the battery lock solenoid will be set to turn OFF.
            If 1, the battery lock solenoid will be set to turn ON. 
            If None, the battery lock solenoid will remain unchanged. 
            Default is None.

        led_strip_state : None or {0, 1, 2, 3, 4}
            New state to which the LED strip is going to be set. 
            If 0, the LED strip will be set to turn OFF.
            If 1, the LED strip will be set to turn RED. 
            If 2, the LED strip will be set to turn GREEN. 
            If 3, the LED strip will be set to turn BLUE. 
            If None, the LED strip will remain unchanged. 
            Default is None.
    
        canMsg_priority_level : None or int
            Priority level given to the message being sent. Must be a number between 1 and 7. The lower the number, the higher the 
            priority. Deafult is None, which means that canMsg_priority_level = {self.default_byCommand_priorities[1] - self.states["extra_priority_level"][-1]}.
            
        Returns
        -------
        None

        """

        activity_code = 1
        if canMsg_priority_level is None:
            canMsg_priority_level_  = self.default_byCommand_priorities[activity_code] 
            try:
                canMsg_priority_level_ -= self.states["extra_priority_level"][-1]
            except IndexError:
                pass
        else:
            canMsg_priority_level_ = canMsg_priority_level

        

        canMsg = Message(data=[0,0,0,0,0,0,0,0])
        canMsg.is_extended_id = True
        canMsg.arbitration_id = create_canMsg_canId(priority_level      = canMsg_priority_level_,
                                                    activity_code       = activity_code,
                                                    destination_address = self.address, 
                                                    origin_address      = CONTROL_CENTER_ADDRESS)
        
        print(canMsg.arbitration_id)
        
        bitmask = 0

        if relay_state is not None:
            bitmask |= 0b0001
            canMsg.data[1] = relay_state

        if door_lock_solenoid_state is not None:
            bitmask |= 0b0010
            canMsg.data[2] = door_lock_solenoid_state

        if battery_lock_solenoid_state is not None:
            bitmask |= 0b0100
            canMsg.data[3] = battery_lock_solenoid_state

        if led_strip_state is not None:
            bitmask |= 0b1000
            canMsg.data[4] = led_strip_state

        canMsg.data[0] = bitmask


        self.send_canMsg(canMsg)
        
        return None
    

    def byCommand_request_module_states(self, canMsg_priority_level : Union[None, int] = None) -> None:

        """
        Send a canMsg obj over the canBus with information required to request immediate send-over of the module states of the
        'individual control module' with address = {self.address}.

        Parameters
        ----------
        canMsg_priority_level : None or int
            Priority level given to the message being sent. Must be a number between 1 and 7. The lower the number, the higher the 
            priority. Deafult is None, which means that canMsg_priority_level = {self.default_byCommand_priorities[2] - self.states["extra_priority_level"][-1]}.
            
        Returns
        -------
        None

        """

        activity_code = 2
        if canMsg_priority_level is None:
            canMsg_priority_level_  = self.default_byCommand_priorities[activity_code] 
            try:
                canMsg_priority_level_ -= self.states["extra_priority_level"][-1]
            except IndexError:
                pass
        else:
            canMsg_priority_level_ = canMsg_priority_level

        

        canMsg = Message(data=[0,0,0,0,0,0,0,0])
        canMsg.is_extended_id = True
        canMsg.arbitration_id = create_canMsg_canId(priority_level      = canMsg_priority_level_,
                                                    activity_code       = activity_code,
                                                    destination_address = self.address, 
                                                    origin_address      = CONTROL_CENTER_ADDRESS)
        
        self.send_canMsg(canMsg)

        return None


    def byCommand_request_battery_data(self, canMsg_priority_level : Union[None, int] = None) -> None:

        """
        Send a canMsg obj over the canBus with information required to request immediate send-over of the battery data of the
        'individual control module' with address = {self.address}.

        Parameters
        ----------
        canMsg_priority_level : None or int
            Priority level given to the message being sent. Must be a number between 1 and 7. The lower the number, the higher the 
            priority. Deafult is None, which means that canMsg_priority_level = {self.default_byCommand_priorities[3] - self.states["extra_priority_level"][-1]}.
            
        Returns
        -------
        None

        """

        activity_code = 3
        if canMsg_priority_level is None:
            canMsg_priority_level_  = self.default_byCommand_priorities[activity_code] 
            try:
                canMsg_priority_level_ -= self.states["extra_priority_level"][-1]
            except IndexError:
                pass
        else:
            canMsg_priority_level_ = canMsg_priority_level

        

        canMsg = Message(data=[0,0,0,0,0,0,0,0])
        canMsg.is_extended_id = True
        canMsg.arbitration_id = create_canMsg_canId(priority_level      = canMsg_priority_level_,
                                                    activity_code       = activity_code,
                                                    destination_address = self.address, 
                                                    origin_address      = CONTROL_CENTER_ADDRESS)
        
        self.send_canMsg(canMsg)

        return None
    
    
    def byCommand_request_timeouts(self, canMsg_priority_level : Union[None, int] = None) -> None:

        """
        Send a canMsg obj over the canBus with information required to request immediate send-over of the timeouts of the
        'individual control module' with address = {self.address}.

        Parameters
        ----------

        canMsg_priority_level : None or int
            Priority level given to the message being sent. Must be a number between 1 and 7. The lower the number, the higher the 
            priority. Deafult is None, which means that canMsg_priority_level = {self.default_byCommand_priorities[4] - self.states["extra_priority_level"][-1]}.
            
        Returns
        -------
        None

        """

        activity_code = 4
        if canMsg_priority_level is None:
            canMsg_priority_level_  = self.default_byCommand_priorities[activity_code] 
            try:
                canMsg_priority_level_ -= self.states["extra_priority_level"][-1]
            except IndexError:
                pass
        else:
            canMsg_priority_level_ = canMsg_priority_level

        

        canMsg = Message(data=[0,0,0,0,0,0,0,0])
        canMsg.is_extended_id = True
        canMsg.arbitration_id = create_canMsg_canId(priority_level      = canMsg_priority_level_,
                                                    activity_code       = activity_code,
                                                    destination_address = self.address, 
                                                    origin_address      = CONTROL_CENTER_ADDRESS)
        
        self.send_canMsg(canMsg)

        return None
    

    def byCommand_set_timeouts(self, 
                               send_module_states_timeout : Union[None, int] = None, 
                               send_battery_data_timeout  : Union[None, int] = None, 
                               bms_connection_timeout     : Union[None, int] = None,
                               canMsg_priority_level      : Union[None, int] = None) -> None:
        

        """
        Send a canMsg obj over the canBus with information required to set the timeouts of the
        'individual control module' with address = {self.address}.

        Parameters
        ----------
        send_module_states_timeout : None or int
            Time interval [ms] in between which the 'individual control module' is set to send its module states over the can bus. 
            If int, the time interval will be set to the number specified, as long as it is between 0 and 65535.
            If None, the time interval will remain unchanged. 
            Default is None.

        send_battery_data_timeout : None or int
            Time interval [ms] in between which the 'individual control module' is set to send its battery data over the can bus. 
            If int, the time interval will be set to the number specified, as long as it is between 0 and 65535.
            If None, the time interval will remain unchanged. 
            Default is None.

        bms_connection_timeout : None or int
            Time interval [ms] after which the 'individual control module' is set to report an error of the BMS connection. 
            If int, the time interval will be set to the number specified, as long as it is between 0 and 65535.
            If None, the time interval will remain unchanged. 
            Default is None.

        canMsg_priority_level : None or int
            Priority level given to the message being sent. Must be a number between 1 and 7. The lower the number, the higher the 
            priority. Deafult is None, which means that canMsg_priority_level = {self.default_byCommand_priorities[5] - self.states["extra_priority_level"][-1]}.
            
        Returns
        -------
        None

        """
        

        activity_code = 5
        if canMsg_priority_level is None:
            canMsg_priority_level_  = self.default_byCommand_priorities[activity_code] 
            try:
                canMsg_priority_level_ -= self.states["extra_priority_level"][-1]
            except IndexError:
                pass
        else:
            canMsg_priority_level_ = canMsg_priority_level

        

        canMsg = Message(data=[0,0,0,0,0,0,0,0])
        canMsg.is_extended_id = True
        canMsg.arbitration_id = create_canMsg_canId(priority_level      = canMsg_priority_level_,
                                                    activity_code       = activity_code,
                                                    destination_address = self.address, 
                                                    origin_address      = CONTROL_CENTER_ADDRESS)
        
        bitmask = 0

        if send_module_states_timeout is not None:

            bitmask |= 0b0001
            byte_data = hex(send_module_states_timeout)[2:]

            if len(byte_data) < 3:
                byte0 = int(byte_data, 16)
                byte1 = 0
            else:
                byte0 = int(byte_data[-2:], 16)
                byte1 = int(byte_data[:-2], 16)

            canMsg.data[1] = byte0
            canMsg.data[2] = byte1


        if send_battery_data_timeout is not None:

            bitmask |= 0b0010
            byte_data = hex(send_battery_data_timeout)[2:]

            if len(byte_data) < 3:
                byte0 = int(byte_data, 16)
                byte1 = 0
            else:
                byte0 = int(byte_data[-2:], 16)
                byte1 = int(byte_data[:-2], 16)

            canMsg.data[3] = byte0
            canMsg.data[4] = byte1


        if bms_connection_timeout is not None:

            bitmask |= 0b0100
            byte_data = hex(bms_connection_timeout)[2:]
            if len(byte_data) < 3:
                byte0 = int(byte_data, 16)
                byte1 = 0
            else:
                byte0 = int(byte_data[-2:], 16)
                byte1 = int(byte_data[:-2], 16)

            canMsg.data[5] = byte0
            canMsg.data[6] = byte1

        canMsg.data[0] = bitmask


        self.send_canMsg(canMsg)
        
        return None
    

    def byCommand_set_extra_priority_level(self, extra_priority_level : int, canMsg_priority_level : Union[None, int] = None) -> None:

        """
        Send a canMsg obj over the canBus with information required to set the extra priority level of the
        'individual control module' with address = {self.address}.

        Parameters
        ----------
        extra_priority_level : {1, 2, 3}
            Number detailing the amount of extra priority that should be given to messages coming from and to the 'individual control module'
            with address = {self.address}. The higher the number, the greater the extra priority.

        canMsg_priority_level : None or int
            Priority level given to the message being sent. Must be a number between 1 and 7. The lower the number, the higher the 
            priority. Deafult is None, which means that canMsg_priority_level = {self.default_byCommand_priorities[6] - self.states["extra_priority_level"][-1]}.
            
        Returns
        -------
        None

        """

        activity_code = 6
        if canMsg_priority_level is None:
            canMsg_priority_level_  = self.default_byCommand_priorities[activity_code] 
            try:
                canMsg_priority_level_ -= self.states["extra_priority_level"][-1]
            except IndexError:
                pass
        else:
            canMsg_priority_level_ = canMsg_priority_level

        

        canMsg = Message(data=[extra_priority_level,0,0,0,0,0,0,0])
        canMsg.is_extended_id = True
        canMsg.arbitration_id = create_canMsg_canId(priority_level      = canMsg_priority_level_,
                                                    activity_code       = activity_code,
                                                    destination_address = self.address, 
                                                    origin_address      = CONTROL_CENTER_ADDRESS)

        self.send_canMsg(canMsg)

        return canMsg
    

    def byCommand_reset_bms_connection(self, bms_reset_duration : int, canMsg_priority_level : Union[None, int] = None) -> None:

        """
        Send a canMsg obj over the canBus with information required to reset the BMS connection fof the 
        'individual control module' with address = {self.address}, for a given amount of time.

        Parameters
        ----------
        bms_reset_duration : {int
            Time duration of the reset process [ms]. It must be a number between 0 and 65535.

        canMsg_priority_level : None or int
            Priority level given to the message being sent. Must be a number between 1 and 7. The lower the number, the higher the 
            priority. Deafult is None, which means that canMsg_priority_level = {self.default_byCommand_priorities[6] - self.states["extra_priority_level"][-1]}.
            
        Returns
        -------
        None

        """

        activity_code = 7
        if canMsg_priority_level is None:
            canMsg_priority_level_  = self.default_byCommand_priorities[activity_code] 
            try:
                canMsg_priority_level_ -= self.states["extra_priority_level"][-1]
            except IndexError:
                pass
        else:
            canMsg_priority_level_ = canMsg_priority_level

        

        canMsg = Message(data=[0,0,0,0,0,0,0,0])
        canMsg.is_extended_id = True
        canMsg.arbitration_id = create_canMsg_canId(priority_level      = canMsg_priority_level_,
                                                    activity_code       = activity_code,
                                                    destination_address = self.address, 
                                                    origin_address      = CONTROL_CENTER_ADDRESS)
        

        byte_data = hex(bms_reset_duration)[2:]
        if len(byte_data) < 3:
            byte0 = int(byte_data, 16)
            byte1 = 0
        else:
            byte0 = int(byte_data[-2:], 16)
            byte1 = int(byte_data[:-2], 16)

        canMsg.data[0] = byte0
        canMsg.data[1] = byte1


        self.send_canMsg(canMsg)
        
        return None




#%%
        
if __name__ == '__main__':

    import os
    import can
    import time

    can.rc['interface'] = 'socketcan'
    can.rc['channel'] = 'can0'
    can.rc['bitrate'] = 250000

    print('\n\rCAN Rx test')
    print('Bring up CAN0....')
    os.system("sudo /sbin/ip link set can0 up type can bitrate 250000")
    time.sleep(0.1)	


    def send_one():

        with can.Bus() as bus:

            canMsg = Message(data=[1,2,3,4,5,6,7,8])
            canMsg.is_extended_id = True
            canMsg.arbitration_id = create_canMsg_canId(priority_level  = 1,
                                                    activity_code       = 55,
                                                    destination_address = 2, 
                                                    origin_address      = 9)
            
            try:
                bus.send(canMsg)
                print(f'Message sent on {bus.channel_info}')
            except:
                print('Message NOT sent')

        return None

try:
    time.sleep(1                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            )
    send_one()
    time.sleep(1)
	
	
except KeyboardInterrupt:
	#Catch keyboard interrupt
	os.system("sudo /sbin/ip link set can0 down")
	print('\n\rKeyboard interrtupt')







    


   


    
    


        

    




   