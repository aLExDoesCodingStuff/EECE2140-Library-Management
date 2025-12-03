# persistence.py

# -*- coding: utf-8 -*-\

import pickle
from models.library import Library
from auth.access_control import AccessControl # Needed for new Library initialization

PICKLE_FILENAME = "catalogSystem.pkl"

def load_state(filepath_csv):
    """
    Loads the Library object and User registry from a pickle file.
    Initializes a new system if the file is not found.
    
    Returns: (library_object, userbase_dictionary)
    """
    try:
        with open(PICKLE_FILENAME, 'rb') as f:
            # We save and load a tuple: (Library object, userbase dictionary {ID: User_object})
            # This step loads all library data and all user objects
            library, userbase = pickle.load(f)
            print(f"[PERSISTENCE] State loaded from {PICKLE_FILENAME}. {len(userbase)} users registered.")
            return library, userbase
    except FileNotFoundError:
        print(f"[PERSISTENCE] No saved state found ({PICKLE_FILENAME}). Initializing new library.")
        
        # 1. Initialize the required access_control argument
        new_ac = AccessControl()
        # 2. Call Library() with the new AccessControl object
        new_library = Library(new_ac) 
        new_library.parse_CSV(filepath_csv) 
        return new_library, {} # Returns new library and an empty userbase
    except Exception as e:
        print(f"[PERSISTENCE] Error loading state: {e}. Starting new library.")
        # Re-try initialization on general error
        new_ac = AccessControl()
        new_library = Library(new_ac) 
        new_library.parse_CSV(filepath_csv)
        return new_library, {}

def save_state(library, userbase):
    """
    Saves the global library object and userbase using pickle.
    """
    try:
        # Saving the tuple containing the Library and the Userbase ensures
        # all book data, user data, and user roles are saved.
        data_to_save = (library, userbase)
        with open(PICKLE_FILENAME, 'wb') as f:
            pickle.dump(data_to_save, f)
        print(f"[PERSISTENCE] Library state successfully saved to {PICKLE_FILENAME}.")
        return True
    except Exception as e:
        print(f"[PERSISTENCE ERROR] Failed to save library data: {e}")
        return False
