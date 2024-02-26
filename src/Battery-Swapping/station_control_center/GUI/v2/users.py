#%%                       IMPORTATION OF MODULES
import pickle
import warnings
import pandas as pd
from datetime import datetime

#%%                      DEFINITION OF AUXILLIARY FUNCTIONS

def load_database(database_path):
    with open(database_path, 'rb') as inp:
        database = pickle.load(inp)
    return database


def save_database(database, database_path):
    with open(database_path, 'wb') as outp:
        pickle.dump(database, outp, protocol=pickle.HIGHEST_PROTOCOL)
    return None

#%%                      DEFINITION OF USER CLASS

class User:
    def __init__(self, id, super_access = False, max_num_batts = 2):

        self.id = id
        self.super_access = super_access
        self.max_num_batts = max_num_batts
        
        self.first_name = None
        self.last_name = None
        self.email = None
        self.age = None

        self.init_history()

        return None


    @property
    def full_name(self):
        return f"{str(self.first_name)} {str(self.last_name)}".replace("None", "")
    
    def init_history(self):
        self.history = pd.DataFrame(columns=["Date", "Action", "No. Batteries", "Warnings"], index = range(1))
        self.history.loc[0, "Date"] = datetime.now()
        self.history.loc[0, "Action"] = "Created"
        self.history.loc[0, "No. Batteries"] = 0
        self.history.loc[0, "Warnings"] = None
        return None

    def add_battery_entry_to_history(self):
        iindex = self.history.shape[0]
        self.history.loc[iindex, "Date"] = datetime.now()
        self.history.loc[iindex, "Action"] = "Entry"
        self.history.loc[iindex, "No. Batteries"] = self.history.loc[iindex - 1, "No. Batteries"] + 1
        self.history.loc[iindex, "Warnings"] = self.generate_history_warning(iindex)
        return None
        
    def add_battery_withdrawal_to_history(self):
        iindex = self.history.shape[0]
        self.history.loc[iindex, "Date"] = datetime.now()
        self.history.loc[iindex, "Action"] = "Withdrawal"
        self.history.loc[iindex, "No. Batteries"] = self.history.loc[iindex - 1, "No. Batteries"] - 1
        self.history.loc[iindex, "Warnings"] = self.generate_history_warning(iindex)
        return None
    
    def generate_history_warning(self, iindex):
        msg = None

        if self.history.loc[iindex, "No. Batteries"] < 0:
            msg = "Unreal number of batteries owed"
            warnings.warn(msg)

        elif self.history.loc[iindex, "No. Batteries"] > self.max_num_batts:
            msg = "User exceeds maximum number of batteries specifed."
            warnings.warn(msg)

        return msg
    
    def remove_last_action_from_history(self):
        iindex = self.history.shape[0] - 1
        self.history.drop(self.history.index[iindex], inplace=True)
        return None
    

#%%                               INITIALIZATION OF DATABASE

if __name__ == '__main__':
    import pickle

    database = {}

    user_id = 220814420323
    database[user_id] = User(user_id)
    database[user_id].first_name = "Andrés Yesid"
    database[user_id].last_name  = "Moreno Villa"

    user_id = 604026517727
    database[user_id] = User(user_id)
    database[user_id].first_name = "Pedro Vélez"
    database[user_id].last_name  = "Aristizabal"
    database[user_id].add_battery_entry_to_history()
    database[user_id].add_battery_entry_to_history()
    database[user_id].add_battery_entry_to_history()

    user_id = 3333
    database[user_id] = User(user_id, super_access=True)
    database[user_id].first_name = "Jhon"
    database[user_id].last_name  = "Doe"

    save_database(database, "database.pkl")