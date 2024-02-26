def bitRead(x : int, n : int) -> int:
    """
    Read a bit of a number.

    Parameters
    ----------
    x : int
        The number from which to read.

    n : int
        Which bit to read, starting at 0 for the least-significant (rightmost) bit.

    Returns
    -------
    res : {0, 1}

    """
    try:
        res = int(bin(x)[2:][-n-1])
    except IndexError:
        res = 0

    return res

def create_canMsg_canId(priority_level, activity_code, destination_address, origin_address):
    canId = 0
    canId |= origin_address
    canId |= destination_address << 8
    canId |= (activity_code & 0xFF) << 16
    for i in range(3):
        canId |= ((priority_level >> i) & 0x01) << (26 + i)
    #canId |= 0x80000000
    return canId

def get_priority_level_from_canMsg_canId(canId):
    priorityLevel = 0
    for i in range(3):
        priorityLevel |= ((canId >> (26 + i)) & 0x01) << i
    return priorityLevel

def get_activity_code_from_canMsg_canId(canId):
    activityCode = 0
    for i in range(8):
        activityCode |= ((canId >> (16 + i)) & 0x01) << i
    return activityCode

def get_destination_address_from_canMsg_canId(canId):
    destinationAddress = 0
    for i in range(8):
        destinationAddress |= ((canId >> (8 + i)) & 0x01) << i
    return destinationAddress

def get_origin_address_from_canMsg_canId(canId):
    originAddress = 0
    for i in range(8):
        originAddress |= ((canId >> i) & 0x01) << i
    return originAddress

