import numpy as np
from tinydb import TinyDB, Query 

User = Query()
db = TinyDB("user_database.json")
VALID_USER_INFO_FIELDS = ["cardId", "firstName", "lastName", "email", "cel", "superAccess", "maxNumBatts", "NumBatts"]



def addUser(cardId, firstName, lastName, email, cel, superAccess = False):
    userInfo = {
        "cardId"      : cardId,
        "firstName"   : firstName,
        "lastName"    : lastName,
        "email"       : email,
        "cel"         : cel,
        "superAccess" : superAccess,
        "maxNumBatts" : None,
        "NumBatts"    : 0
    }
    if not superAccess:
        userInfo["maxNumBatts"] = 2

    db.insert(userInfo)
    return None

def getUser(userInfoToMatch):
    userInfoToMatch_ = {key:value for key,value in userInfoToMatch.items() if key in VALID_USER_INFO_FIELDS}
    return db.search(User.fragment(userInfoToMatch_))

def updateUser(userInfoToMatch, userInfoToUpdate):
    userInfoToMatch_ = {key:value for key,value in userInfoToMatch.items() if key in VALID_USER_INFO_FIELDS}
    userInfoToUpdate = {key:value for key,value in userInfoToUpdate.items() if key in VALID_USER_INFO_FIELDS}
    db.update(userInfoToUpdate, User.fragment(userInfoToMatch_))
    return None



if __name__ == "__main__":
    db.truncate()
    addUser(1010102314, "Andrés Yesid", "Moreno Villa", "aymorenov@eafit.edu.co", 3207674005)

    print(getUser({"cardId":1010102314}))
    print(getUser({"cardId":1010102314, "superAccess":True}))

    updateUser({"cardId":1010102314}, {"superAccess":True})
    print(getUser({"cardId":1010102314, "superAccess":True}))
    
    updateUser({"cardId":1010102314}, {"superAccess_":True})
    print(getUser({"cardId":1010102314, "superAccess":True}))
    
    updateUser({"cardId":10101023145}, {"superAccess_":False})
    print(getUser({"cardId":1010102314, "superAccess":False}))