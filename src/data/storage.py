#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  2 16:38:43 2025

@author: alexmessier
"""
import sys
from pathlib import Path

if Path.cwd().parent not in sys.path:
    sys.path.append(Path.cwd().parent)

from auth.access_control import AccessControl
from models.user_manager import UserManager
from models.user import User
from models.library import Library
from datetime import date
from datetime import timedelta
import random 
import pandas as pd
import numpy as np




class SaveManager:
    
    def __init__(self):
        self.user_records_path = "data/user_records.csv" 
        self.loan_records_path = "data/loan_records.csv"
        self.waitlist_records_path = "data/waitlist_records.csv"
        self.pending_holds_records_path = "data/pending_holds_records"
        

#Persistence methods
    
    # reads  data from user_records.csv, passes a list of User objects to UserManager
    def load_users(self, user_manager:UserManager,access_control:AccessControl):
        try:
            df_user_records = pd.read_csv("data/user_records.csv")
            users = []
            tally = 0
            for index,row in df_user_records.iterrows():
                user_id = row["user_id"]
                name = row["name"]
                # matches user's roles (stored as strings like "member","admin" against an available list of roles stored in access_control class
                # ^ this feels like a really shit design solution btw.
                roles = []
                role_list = row["roles"].split(",")
                for r in role_list:
                    for t in access_control.role_types:
                        if r == t.name: roles.append(t)
                access_control.assign_role(user_id,roles)
                user = User(name,user_id)
                users.append(user)
                tally+=1
                
            # pass list of user objects to UserManager to store in its internal registry
            user_manager.load_users(users)
            print(f">>> Loaded {tally} user records from '{self.user_records.csv}'.")
        except FileNotFoundError:
            print("File Not Found.")
            
    
    # writes user_manager.users to CSV 
    def save_users(self, user_manager:UserManager,access_control:AccessControl):
        user_list = []
        for user in user_manager.users.values():
            record = {
                "user_id": user.user_id,
                "name":user.username,
                "roles":access_control.roles_as_str(user.user_id)
                }
            user_list.append(record)
        users_df = pd.DataFrame(user_list)
        if len(users_df) > 0:
            users_df.to_csv(self.user_records_path, index=False)
            print(f"\nSuccessfully saved {len(users_df)} records to {self.user_records_path}.")
        else:
            print("\nNo checked out items to save.")
         
    # reads loan records from CSV, passes a dict of current loans to library.current_loans
    def load_loans(self,library:Library,user_manager:UserManager):
        try:
            df_loan_records = pd.read_csv(self.loan_records_path)
            tally = 0
            for index,row in df_loan_records.iterrows():
                loan_number = row["loan_number"]
                user_id = row["user_id"]
                user = user_manager.users[user_id]
                item_id = row["item_id"]
                borrow_date = date.fromisoformat(row["borrow_date"])
                return_date = date.fromisoformat(row["return_date"])
                
                # find an available copy of the book
                book = library.search_by_id(item_id)
                copy = library.find_available_copy(book)
                library.process_checkout(loan_number,user,book,copy,borrow_date,return_date)
                tally+=1
            print(f">>> Loaded {tally} outstanding loans from '{self.user_records_path}'.")
        except FileNotFoundError:
            print("Error: File Not Found.")
        except pd.errors.EmptyDataError:
            print("There are no outstanding loan records to restore.")
                
    # writes library.current_loans to CSV
    def save_loans(self,library:Library):
        loans_df = pd.DataFrame([
            {"loan_number": loan_number, **loan_info}
            for loan_number, loan_info in library.current_loans.items()
        ])            
        loans_df.to_csv(self.loan_records_path, index=False)
        print(f"\nSuccessfully saved {len(loans_df)} records to {self.loan_records_path}.")
       
   
    
    def save_waitlists(self,library:Library):
        try:
            master_waitlist = []
            for book in library.inventory:
                if len(book.waitlist.queue)>0:
                    for user in book.waitlist.queue:
                        record = {}
                        record["item_id"] = book.id
                        record["user_id"] = user.user_id
                        record["position"] = book.waitlist.queue.index(user)+1
                        master_waitlist.append(record)
            master_waitlist_df = pd.DataFrame(master_waitlist)
            master_waitlist_df.to_csv(self.waitlist_records_path)
        except FileNotFoundError:
            print("Error: Destination File Not Found!")
        except pd.errors.EmptyDataError:
            print("No waitlist data to store.")
            
    def load_waitlists(self,library:Library,user_manager:UserManager):
        try: 
            master_waitlist_df = pd.read_csv(self.waitlist_records_path)
            unique_item_ids = set(master_waitlist_df["item_id"])
            tally = 0
            for item_id in unique_item_ids:
                # get a subset of the master_waitlist dataframe for a certain book, sorted by waitlist position as a list
                sorted_userIDs_by_item = master_waitlist_df[master_waitlist_df["item_id"]==item_id].sort_values("position")["user_id"].to_list()
                book = library.search_by_id(item_id)
                for user_id in sorted_userIDs_by_item:
                    user = user_manager.users[user_id]
                    book.waitlist.add_to_queue(user)
                    user.items_on_hold.append(book)
                    tally+=1
            print(f">>> Loaded {tally} waitlist records from {self.waitlist_records_path}")
        except FileNotFoundError:
            print("Error: Source File Not Found!")
            
    def save_pending_holds(self, library:Library):
        try:
            master_df = []
            for book in library.inventory:
                if len(book.waitlist.holds_pending)>0:
                    for user,checkout_window in book.waitlist.holds_pending:
                        record = {}
                        record["item_id"] = book.id
                        record["user_id"] = user.user_id
                        record["checkout_window"] = checkout_window
                        master_df.append(record)
            master_df = pd.DataFrame(master_df)
            master_df.to_csv(self.pending_holds_records_path)
        except FileNotFoundError:
            print("Error: Destination File Not Found!")
        except pd.errors.EmptyDataError:
            print("No pending hold records to store.")
            
    def load_pending_holds(self,library:Library,user_manager:UserManager):
        try:
            df_pending_holds = pd.read_csv(self.pending_holds_records_path)
            holds = []
            tally = 0
            for index,row in df_pending_holds.iterrows():
                item_id = row["item_id"]
                user_id = row["user_id"]
                checkout_window = date.fromisoformat(row["checkout_window"])
                book = library.search_by_id(item_id)
                user = user_manager.users[user_id]
                book.waitlist.holds_pending.add((user,checkout_window))
                tally+=1
            print(f">>> Loaded {tally} pending hold recorrds from '{self.pending_holds_records_path}'.")
        except FileNotFoundError:
            print("File Not Found.")
        

# save_manager = SaveManager()
# df = pd.read_csv(save_manager.waitlist_record_path)



    
    
    
    
    
    
    