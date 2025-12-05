#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

from collections import deque
from datetime import timedelta
from datetime import date
import pandas as pd
from inspect import getmembers, isfunction
import random 
import numpy as np

# add the src folder to search path (make imports not break)
base_directory = Path.cwd()
# print(base_directory)
if base_directory not in sys.path:
    sys.path.append(base_directory)

from models.library import Library
from models.user import User
from models.book import Book
from models.waitlist import Waitlist
from models.user_manager import UserManager
from auth.role import Role
from auth.access_control import AccessControl
from interface.gui import *
from data.storage import SaveManager

 ## SETUP/STATE RECALL STUFF ===============================
dataset_filepath = base_directory.parent/"Sample Datasets"/"books_new.csv"

save_manager = SaveManager() #Setup SaveManager

user_manager = UserManager() #Setup UserManager

#Setup RBAC
member_role = Role("member",["checkout_item","return_item"])  
admin_role = Role("admin",["add_item","remove_item","process_checkout","get_days_overdue","get_overdue_copies","check_overdue","catalog_system","list_inv","load_state","save_state","set_date"])
print()

# Initialize Library
access_control = AccessControl([member_role,admin_role])
library = Library(access_control)

# Restore library inventory
# admin = user_manager.users[8]
library.parse_CSV(dataset_filepath,"admin")

# Restore users,loans from Previous State
# save_manager.load_users(user_manager,access_control)
# save_manager.load_loans(library,user_manager)
# save_manager.load_waitlists(library,user_manager)
print("# ================================================================")
print()

# library.clear_all_loans(user_manager)

# ================================================================

# user1 = user_manager.users[1]
# user2 = user_manager.users[2]
# user3 = user_manager.users[3]
# user4 = user_manager.users[4]
# user5 = user_manager.users[6]
# user6 = user_manager.users[7]

# book1 = library.search_by_id(0)
# book2 = library.search_by_id(1)
# book3 = library.search_by_id(2)
# book4 = library.search_by_id(3)

# print(book1.waitlist.print_str())
# print(book2.waitlist.print_str())
# print(book3.waitlist.print_str())
# print(book4.waitlist.print_str())




# # test checking out some books
# library.checkout_item(book1, user1)
# library.checkout_item(book1, user2)
# library.checkout_item(book1, user3)
# library.checkout_item(book1, user4)
# library.checkout_item(book1, user5)
# library.checkout_item(book1, user6)

# library.checkout_item(book2, user1)
# library.checkout_item(book2, user2)
# library.checkout_item(book2, user3)
# library.checkout_item(book2, user4)
# library.checkout_item(book2, user5)

# library.checkout_item(book3, user2)
# library.checkout_item(book3, user3)
# library.checkout_item(book3, user4)
# library.checkout_item(book3, user5)
# library.checkout_item(book3, user6)

# library.checkout_item(book4, user1)
# library.checkout_item(book4, user2)
# library.checkout_item(book4, user3)
# library.checkout_item(book4, user4)
# library.checkout_item(book4, user5)
# library.checkout_item(book4, user6)



# # generate some testing data
# print()
# user_id = np.arange(0,100)
# item_id = np.random.randint(0,6,size=100)
# position = np.random.randint(0,4,size=100)
# d = {"user_id":user_id,"item_id":item_id,"position":position}
# df1 = pd.DataFrame(d)

# df1 = df1.sort_values("item_id")
# print(df1.iloc[0:30])




# =============================================================================


save_manager.save_users(user_manager,library.access_control)
save_manager.save_loans(library)
save_manager.save_waitlists(library)



# Create some users

# user_manager.create_user("John",member_role,library.access_control)
# user_manager.create_user("admin",[admin_role,member_role],library.access_control)

