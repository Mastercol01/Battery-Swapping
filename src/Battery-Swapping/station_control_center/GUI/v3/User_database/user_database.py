import os
import numpy as np
from tinydb import TinyDB, Query 

db_path = os.path.dirname(__file__)
db_path = os.path.join(db_path, "user_database.json")

User = Query()
db = TinyDB(db_path)
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

def getUsers(userInfoToMatch):
    userInfoToMatch_ = {key:value for key,value in userInfoToMatch.items() if key in VALID_USER_INFO_FIELDS}
    return db.search(User.fragment(userInfoToMatch_))

def updateUsers(userInfoToMatch, userInfoToUpdate):
    userInfoToMatch_ = {key:value for key,value in userInfoToMatch.items() if key in VALID_USER_INFO_FIELDS}
    userInfoToUpdate = {key:value for key,value in userInfoToUpdate.items() if key in VALID_USER_INFO_FIELDS}
    db.update(userInfoToUpdate, User.fragment(userInfoToMatch_))
    return None


def _createInitialListOfUsers():
    db.truncate()
    addUser(1779216653, "Andrés Yesid", "Moreno Villa",      "andresmoreno@email.com",   5550123456, superAccess = False)
    addUser(1018734958, "Pedro",        "Vélez Aristizábal", "pedrovelez@email.com",     2226789012, superAccess = False)
    addUser(1742157924, "Gilberto",     "Osorio",            "gilbertoosorio@email.com", 3335432198, superAccess = False)
    addUser(1742157924, "Ricardo",      "Mejía Gutiérrez",   "ricardomejia@email.com",   4447890321, superAccess = False)
    return None



if __name__ == "__main__":
    if True:
        _createInitialListOfUsers()

