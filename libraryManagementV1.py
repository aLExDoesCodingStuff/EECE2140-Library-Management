#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
from datetime import timedelta
from datetime import date
import numpy as np
from pathlib import Path
import pandas as pd



base_directory = Path(__file__).parent
filename = "Sample Datasets/books_new.csv"
filepath = base_directory/filename


class Library:
    
    def __init__(self):
        self.inventory = []
        self.current_date = date.today()
        self.default_checkout_window = 7 # days
        
    
    def listInv(self):
        counter = 1
        for book in self.inventory:
            print(f"{counter}.",book)
            counter+=1
            
        
    # Checks out a book from the library's inventory. 
    def checkout_item(self,book,user):
        # Check if the user already has the book in their hold list
        if book in user.items_on_hold:
            # if the user has already been through the waitlist (and is finally picking the book up)
            for u,window in book.waitlist.holds_pending:
                if u == user:
                    self.process_checkout(book,user)
                    print(f"{user.username} checked out: {book.name} by {book.author}.")
                    book.waitlist.holds_pending.remove(u,window)
                    return
              
            # else its a duplicate hold request from someone in the waitlist already
            print(f"{user} has already placed {book.name} by {book.author} on hold, and is in the waitlist (current position: {book.waitlist.get_pos(user)})")
            return
        
        # Check to see if there is a waitlist active. If so, join the waitlist.
        if len(book.waitlist.queue)>0:
            pos = book.waitlist.add_to_queue(user)
            user.items_on_hold.append(book)
            print(f"All Copies of {book.name} by {book.author} are currently on hold. Added {user.username} to the waitlist (current position: {pos}). ")
            return
        
        # If there's no active waitlist, check the list of copies to see if the book is available.
        counter = 0
        while counter < len(book.copies):
           if book.copies[counter]["borrowed_by"] == None:
               self.process_checkout(book,user,counter)
               print(f"{user.username} checked out: {book.name} by {book.author}.") # Update message to include available remaining copies
               return
           counter+=1
        # if all copies are in use, join the waitlist  
        pos = book.waitlist.add_to_queue(user)
        user.items_on_hold.append(book)
        print(f"All Copies of {book.name} by {book.author} are currently on hold. Added {user.username} to the waitlist (current position: {pos}). ")
         
        
    # tags a book copy with the appropriate information when it is checked out and adds it to the user's checked-out inventory
    def process_checkout(self,book,user,copy_number):
        book.copies[copy_number]["borrowed_by"] = user
        today = self.current_date
        book.copies[copy_number]["borrow_date"] = today
        book.copies[copy_number]["return_date"] = today + timedelta(days=self.default_checkout_window)
        user.items_checked_out.append((book,book.copies[copy_number]))
    
    
  
    # Returns a book to the library's inventory, and assesses late fees if applicable
    def return_item(self,book,user):
        
        # check if the user actually has the book checked out
        copy = None
        for b,c in user.items_checked_out:
            if b == book:
                copy = c
        if copy == None:
            print(f"{user} does not currently have {book.name} checked out.")
            return
            
        # assess late fees (if applicable)
        
        # clear the update the copy information on the book
        copy["borrowed_by"] = None
        copy["borrow_date"] = None
        copy["return_date"] = None
        
        # remove the book from user's items_checked_out list
        for b,c in user.items_checked_out:
            if b == book:
                user.items_checked_out.remove((b,c))
                break
        
        # print a summary
        print(f"{user} returned {book.name}.")
        
       # advance the waitlist
        book.waitlist.advance_waitlist()
        
    # checks a book object for checked-out copies which are overdue
    # returns a list of overdue copies
    def get_overdue_copies(self,book):
        if not isinstance(book,Book):
            raise TypeError
        
        overdue_copies = []
        for copy in book.copies:
            # see if copy is checked out
            if copy["borrowed_by"]!=None:
                if copy["return_date"]<self.current_date or copy["return_date"] == self.current_date:
                    overdue_copies.append(copy)
        return overdue_copies


    def check_overdue(self):
        for book in self.inventory:
            overdue = self.get_overdue_copies(book)
            for copy in overdue:
                days_overdue = self.get_days_overdue(copy)
                print(copy["borrowed_by"],days_overdue)
                
    def get_days_overdue(self,copy):
        return_date = copy["return_date"]
        time_delta = self.current_date - return_date
        days_overdue = time_delta.days
        return days_overdue
    
    
    # bulk add books to inventory from a book dataset (CSV format)
    def parseCSV(self,filePath):
        df = pd.read_csv(filePath,usecols=['Title','Author','Genre'])
        data = df.to_numpy()
        for row in data:
            title = row[0]
            author = row[1]
            genre = row[2]
            self.inventory.append(Book(title,author,genre))
        
        print("Parsed CSV and added items to inventory.")
    
    # modify the current date recognized by the library instance AND related classes
    # * note that directly changing self.current_date would fail to change the date of related classes such as waitlist
    def set_date(self,new_date):
       if not isinstance(new_date,date):
           raise TypeError
       self.current_date = new_date
           
          
        
class Book:
    
    def __init__(self,name,author,genre):
        self.name = name
        self.author = author
        self.genre = genre
        self.copies = self.make_copies(3)
        self.waitlist = Waitlist(self)
        
    def make_copies(self,num_copies):
        copies = []
        for i in range(num_copies):
            copy = {"borrowed_by":None,"borrow_date":None,"return_date":None}
            copies.append(copy)
        return copies
    
    def locate_copies(self):
        info = ""
        for copy in self.copies:
            if copy["borrowed_by"] == None: 
                borrower = "<empty>"
            else:
                borrower = copy["borrowed_by"].username
            if copy["borrow_date"] == None:
                borrow_date = "<empty>"
            else: 
                borrow_date = copy["borrow_date"]
            if copy["return_date"] == None:
                return_date = "<empty>"
            info += borrower + " - " + str(borrow_date) + "," + str(return_date)
        return info
    
    def __str__(self):
         return self.name
     
    def __repr__(self):
        return f"{self.name},'{self.author}',{self.genre},{len(self.copies)}"
        
    
        
class Waitlist:
    def __init__(self,book):
        self.queue = deque()
        self.holds_pending = set()
        self.hold_item = book
        self.default_pending_hold_window = 3 
        
    def __str__(self):
        return self.queue.__str__()
    
    # adds a user to the waitlist and returns their position in queue
    def add_to_queue(self,user):
        self.queue.append(user)
        return len(self.queue)
        
        
    def advance_waitlist(self):
        line_leader = self.queue.popleft()
        checkout_window = self.calculate_checkout_window()
        t = (line_leader,checkout_window)
        self.holds_pending.add(t)
        print(f"{line_leader.username}, a copy of {self.hold_item.name} is now available to check out. You have 3 days to check it out before you automatically forfeit your spot in the waitlist.")

    
    def get_pos(self,user):
        try:
            spot = self.queue.index(user) + 1
            return spot
        except ValueError:
            print(f"{user.username} is not currently in the waitlist.")
     
     
    # notifies the 1st user (leader) in waitlist when a book copy becomes available to them
    # initiates a timer for leader to checkout a book
    def notify_waitlist_leader(self):
       pass
    
     # returns the end date of the checkout window to collect book on hold
    def calculate_checkout_window(self):
        today = date.today()
        checkout_by = today + timedelta(days=self.default_pending_hold_window)
        return checkout_by
    

    
    # searches waitlist for expired holds(users who failed to check out book within the designated time window after it became available)
    # removes any expired holds found, and prints a message
    # automatically calls notify_waitlist_leader for next users in waitlist
    def check_expired_holds(self,current_date):
        # search through holds_pending set
        for hold in self.holds_pending:
            user = hold[0]
            hold_exp_date = hold[1]
            # if the hold is expired
            if hold_exp_date < current_date:
                # print a message
                print(f"{user.username}'s hold on {self.hold_item.name} is now expired. Removing from waitlist...")
                # remove the hold from holds_pending
                self.holds_pending.remove(hold)
                # remove the item from the user's holds_pending list
                user.holds_pending.remove(self.hold_item)
                # call notify_waitlist_leader
                
                
        
    
    def print_str(self):
        string = ""
        counter = 0
        for item in self.queue:
            string += item.username
            if counter < len(self.queue)-1:
                string += ","
            counter+=1
        return string
            
    
class User: 
    def __init__(self, username:str):
        self.username = username
        self.items_checked_out = []
        self.items_on_hold = []
        
    def print_hold_items(self):
        if len(self.items_on_hold)==0:
            print(f"{self.username} does not currently have any books on hold.")
        else:
            counter = 0
            for book in self.items_on_hold:
                print(f"{counter}. {book}")
    
    def print_checked_out(self):
        if len(self.items_checked_out)==0:
            print(f"{self.username} does not currently have any books on hold")
        else: 
            counter = 0
            for book in self.items_checked_out:
                print(f"{counter}. {book}.")
                counter +=1
                
    def __str__(self):
        return self.username
    
    def __repr__(self):
        return f"username ='{self.username}',items_checked_out={self.items_checked_out},items_on_hold={self.items_on_hold}"
        

# ====================================================================
# TEST CODE: 
    
library = Library()
library.parseCSV(filepath) 

user1 = User("John")
user2 = User("Susan")
user3 = User("Sasha")
user4 = User("Terry")
user5 = User("Anna")
user6 = User("Noelle")

print(library.current_date)


book1 = library.inventory[0]
library.checkout_item(book1,user1) 
library.checkout_item(book1,user2)
library.checkout_item(book1,user3)
print()

library.checkout_item(book1,user4) 
library.checkout_item(book1,user5)
print()

print(book1.waitlist)
print()

library.return_item(book1, user1)

library.checkout_item(book1,user6) # should add Noelle to waitlist

library.return_item(book1,user1)







    



















     
    
        
    
    
    

    
    
    
    
   




