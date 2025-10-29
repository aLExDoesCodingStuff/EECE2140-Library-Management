#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
import time
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
        self.default_checkout_window = 7 #days
        
    
    def listInv(self):
        counter = 1
        for book in self.inventory:
            print(f"{counter}.",book)
            counter+=1
            
        
    # Checks out a book from the library's inventory. 
    def checkout_item(self,book,user):
        
        # Check if the user has already placed a hold on the book 
        if book in user.items_on_hold:
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
               book.copies[counter]["borrowed_by"] = user
               today = self.current_date
               book.copies[counter]["borrow_date"] = today
               book.copies[counter]["return_date"] = date(today.year,today.month,today.day + self.default_checkout_window)
               user.items_checked_out.append((book,book.copies[counter]))
               print(f"{user.username} checked out: {book.name} by {book.author}.") # Update message to include available remaining copies
               return
           counter+=1
           
        # if all copies are in use, join the waitlist  
        pos = book.waitlist.add_to_queue(user)
        user.items_on_hold.append(book)
        print(f"All Copies of {book.name} by {book.author} are currently on hold. Added {user.username} to the waitlist (current position: {pos}). ")
            
    # Returns a book to the library's inventory, and assesses late fees if applicable
    def return_item(self,book,user):
        
        # find the copy of the book in the user's items_checked_out inventory
        copy = None # is this line necessary?
        for b,c in user.items_checked_out:
            if b == book:
                copy = c
        
        # assess late fees (if applicable)
        
        # update the copy information on the book
        copy["borrowed_by"] = None
        copy["borrow_date"] = None
        
        # print a summary
        print(f"{user} returned {book.name}.")
        
        # update the waitlist 
        book.waitlist.notify_waitlist_leader()
      
    # checks the library inventory for overdue items
    def check_overdue():
        pass
        
    
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
    
    # modify the date stored by library instance
    # intended for debugging time-dependent features (eg, hold window)
    # enter new date in the format (YYYY.MM.DD)
    def set_date(self,new_date:str):
        year,month,day = new_date.split('.')
        year,month,day = int(year),int(month),int(day)
        self.current_date = date(year,month,day)
        
                
        
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
        
print("Hello Alex what are you being for halloween dont be lame and say nothing")    
        
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
        
        
    def advance_queue(self):
        if self.queue:
            return self.queue.popleft()
        return None
    def get_pos(self,user):
        try:
            spot = self.queue.index(user) + 1
            return spot
        except ValueError:
            print(f"{user.username} is not currently in the waitlist.")
     
     
    # notifies the 1st user (leader) in waitlist when a book copy becomes available to them
    # initiates a timer for leader to checkout a book
    def notify_waitlist_leader(self):
        
        # send a notification to 1st user
        user = self.queue[0]

        checkout_window = self.calculate_checkout_window()
        t = (user,checkout_window)
        self.holds_pending.add(t)
        
        # need a line to auto-calculate checkout window
        print(f"{user.username}, a copy of {self.hold_item.name} is now available to check out. You have 3 days to check it out before you automatically forfeit your spot in the waitlist.")
    
     # returns the end date of the checkout window to collect book on hold
    def calculate_checkout_window(self):
        today = date.today()
        checkout_by = date(today.year,today.month,today.day+self.default_pending_hold_window)
        return checkout_by
    
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

library.set_date("2025.10.23")  

user1 = User("John")
user2 = User("Susan")
user3 = User("Sasha")
user4 = User("Terry")
user5 = User("Anna")


book1 = library.inventory[0]
library.checkout_item(book1, user1) 
library.checkout_item(book1,user2)
library.checkout_item(book1,user3)
library.checkout_item(book1,user4)
library.checkout_item(book1,user5)
print()
print(book1.waitlist)
print()
library.return_item(book1, user1)
print()
library.checkout_item(book1, user5)




















     
    
        
    
    
    

    
    
    
    
   




