#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

from collections import deque
from datetime import timedelta
from datetime import date
import pandas as pd
from inspect import getmembers, isfunction

# add the src folder to search path (make imports not break)
base_directory = Path.cwd()
# print(base_directory)
if base_directory not in sys.path:
    sys.path.append(base_directory)

from models.library import Library
from models.user import User
from models.book import Book
from models.waitlist import Waitlist
from auth.role import Role
from auth.access_control import AccessControl


dataset_filepath = base_directory.parent/"Sample Datasets"/"books_new.csv"

#Setup RBAC
member_role = Role("member",["checkout_item","return_item"])  
admin_role = Role("admin",["add_item","remove_item","process_checkout","get_days_overdue","get_overdue_copies","check_overdue","catalog_system","list_inv","load_state","save_state","set_date"])
print()

# Initialize Library
ac = AccessControl()
library = Library(ac)
library.parse_CSV(dataset_filepath)
print()


# Create new users
admin = User("admin")
library.ac.assign_role(admin.username, [admin_role,member_role])
print()

member = User("member")
library.ac.assign_role(member.username,member_role)


book = Book("The Wayside School","Louis Sachar","Children")
    


# restore previous state
df = library.load_state(library,"catalogSystem.csv",admin)
print(df.head())
print()

user1 = User("John")
user2 = User("Susan")
user3 = User("Sasha")
user4 = User("Terry")
user5 = User("Anna")
user6 = User("Noelle")
library.ac.assign_role(user1.username, member_role)
library.ac.assign_role(user2.username, member_role)
library.ac.assign_role(user3.username, member_role)
library.ac.assign_role(user4.username, member_role)
library.ac.assign_role(user5.username, member_role)
library.ac.assign_role(user6.username, member_role)
print()

book = library.inventory[0]
library.checkout_item(book,user1) 
library.checkout_item(book,user2)
library.checkout_item(book,user3)
print()

library.checkout_item(book, user4)
library.checkout_item(book, user5)
library.return_item(book,user1)
library.checkout_item(book,user6)
library.checkout_item(book,user4)
library.return_item(book,user2)







list_of_users = [user1,user2,user3,user4,user5,user6]
master_catalog = library.catalog_system(admin,list_of_users)
print()


library.save_state(admin,master_catalog)

