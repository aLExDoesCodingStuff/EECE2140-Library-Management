#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 16:17:45 2025

@author: alexmessier
"""
import sys
from pathlib import Path
from datetime import timedelta
from datetime import date
from pathlib import Path
import pandas as pd
from auth.access_control import AccessControl
from models.book import Book
from models.user_manager import UserManager


class Library:

    # df = pd.read_csv(filename,usecols=['Title','Author','Genre'])
    # filename = df.dropna(axis=0, how='any')
    
    def __init__(self,access_control):
        self.inventory = []
        self.current_loans = {} # dict of dicts
        self.current_date = date.today()
        self.default_checkout_window = 7 # days
        self.access_control = access_control
        self.next_item_ID = 0
        
        
    
    def listInv(self,user):
        # authorization check
        if not self.access_control.has_permission(user.username,"list_inv"):
            raise PermissionError("Access Denied: list_inv")
        counter = 1
        for book in self.inventory:
            print(f"{counter}.",book)
            counter+=1
   
#================================================================
 # USER ACCESSIBLE METHODS     

          
    # Checks out a book from the library's inventory. 
    def checkout_item(self,book,user):
        # check if the user has the member role
        if not self.access_control.has_permission(user.user_id,"checkout_item"):
            raise PermissionError("Access Denied: checkout_item")
       
        
        # Check if the user already has the book in their hold list
        if book in user.items_on_hold:
            # if the user had a pending hold 
            for u,window in book.waitlist.holds_pending:
                if u == user:
                    copy = self.find_available_copy(book)
                    today = self.current_date
                    return_date = today + timedelta(days=self.default_checkout_window)
                    self.process_checkout(None,user,book,copy,today,return_date)
                    print(f"{user.username} checked out: {book.name} by {book.author}.")
                    book.waitlist.holds_pending.remove((u,window))
                    return
              
            # else it's a duplicate hold request from someone in the waitlist already
            print(f"{user} has already placed {book.name} by {book.author} on hold, and is in the waitlist (current position: {book.waitlist.get_pos(user)})")
            return
        
        # Check to see if there is a waitlist active. If so, join the waitlist.
        if len(book.waitlist.queue)>0:
            pos = book.waitlist.add_to_queue(user)
            user.items_on_hold.append(book)
            print(f"All Copies of {book.name} by {book.author} are currently on hold. Added {user.username} to the waitlist (current position: {pos}). ")
            return
        
        # If there's no active waitlist, check the list of copies to see if the book is available.
        copy = self.find_available_copy(book)
        # if an available copy is found, check it out
        if copy != None:
            today = self.current_date
            return_date = today + timedelta(days=self.default_checkout_window)
            self.process_checkout(None,user,book,copy,today,return_date)
            print(f"{user.username} checked out: {book.name} by {book.author}.") # Update message to include available remaining copies
            return
        
        # if all copies are in use, join the waitlist  
        pos = book.waitlist.add_to_queue(user)
        user.items_on_hold.append(book)
        print(f"All Copies of {book.name} by {book.author} are currently on hold. Added {user.username} to the waitlist (current position: {pos}). ")
    
    # Returns a book to the library's inventory, and assesses late fees if applicable
    def return_item(self,book,user):
        # check authorization
        if not self.access_control.has_permission(user.user_id,"return_item"):
            raise PermissionError("Denied access: return_item")
        
        # check if the user actually has the book checked out
        copy = None
        for b,c,l in user.items_checked_out:
            if b == book:
                copy = c
                loan_number = l
        if copy == None:
            print(f"{user} does not currently have {book.name} checked out.")
            return
            
        # assess late fees (if applicable)
        
        # clear the update the copy information on the book
        copy["borrowed_by"] = None
        copy["borrow_date"] = None
        copy["return_date"] = None
        
        # remove the book from user's items_checked_out list
        for b,c,l in user.items_checked_out:
            if b == book:
                user.items_checked_out.remove((b,c,l))
                break
            
        # remove the record of the loan from library.current_loans
        self.current_loans.pop(l)
        
        # print a summary
        print(f"{user} returned {book.name}.")
        
        # advance the waitlist
        book.waitlist.advance_waitlist()    
        
#================================================================  
# ADMIN ACCESSIBLE METHODS  

    # remove a book from the library's inventory
    def remove_item(self,book,user):
        # authorization check
        if not self.access_control.has_permission(user.user_id,"remove_item"):
            raise PermissionError("Access Denied: remove_item")
        
        if not isinstance(book,Book): raise TypeError
        
        # search for book in library inventory. If found, remove it and return True
        if book in self.inventory:
            self.inventory.remove(book)
            return True
        else: return False
    
    # add a book to the library's inventory
    def add_item(self,title,author,genre,user):
        # # authorization check
        # if not self.access_control.has_permission(user.user_id,"add_item"):
        #     raise PermissionError("Access Denied: add_item")
            
        # assign a unique identifier to the book
        book = Book(title,author,genre,self.next_item_ID)
        
        # search for book in library inventory. If not found, add it and return True
        if book not in self.inventory:
            self.inventory.append(book)
            self.next_item_ID+=1
            return True
        else: return False


    # searches for an available copy of a book. if none found, returns None
    def find_available_copy(self,book):
        if not isinstance(book,Book):
            raise TypeError("Argument is not of type 'Book'.")
            
        counter = 0
        while counter < len(book.copies):
            if book.copies[counter]["borrowed_by"] == None:
                return book.copies[counter]
            counter+=1
        return None
      
    # tags a book copy with the appropriate information when it is checked out and adds it to the user's checked-out inventory
    # How to make an argument optional? add an optional loan number for when this method is called from save manager 
    def process_checkout(self,number,user,book,copy,borrow_date,return_date):
        
        copy["borrowed_by"] = user
        copy["borrow_date"] = borrow_date
        copy["return_date"] = return_date
        if number == None:
            loan_number = self.generate_loan_number()
        else: 
            loan_number = number
        user.items_checked_out.append((book,copy,loan_number))
        loan_record = {"user_id":user.user_id,"item_id":book.id,"borrow_date":borrow_date,"return_date":return_date}
        self.current_loans[loan_number]=loan_record
    
    def generate_loan_number(self):
        import random as r
        number = r.randint(0,99999)
        # check for the unlikely case of a duplicate loan number
        while number in self.current_loans:
            number = r.randint(0,99999)
        return number
     
    # search for a book by its ID. Return book object, or None
    def search_by_id(self,searchID):
        for book in self.inventory:
            if book.id == searchID:
                return book
        return None
    
        

    def check_overdue(self,user):
        # authorization check
        if not self.access_control.has_permission(user.user_id,"check_overdue"):
            raise PermissionError("Access Denied: check_overdue")
            
        for book in self.inventory:
            overdue = self.get_overdue_copies(book)
            for copy in overdue:
                days_overdue = self.get_days_overdue(copy)
                print(copy["borrowed_by"],days_overdue)
                
         
    # checks a book object for checked-out copies which are overdue
    # returns a list of overdue copies
    def __get_overdue_copies(self,book):
        
        if not isinstance(book,Book):
            raise TypeError
        
        overdue_copies = []
        for copy in book.copies:
            # see if copy is checked out
            if copy["borrowed_by"]!=None:
                if copy["return_date"]<self.current_date or copy["return_date"] == self.current_date:
                    overdue_copies.append(copy)
        return overdue_copies


    def __get_days_overdue(self,copy):
        return_date = copy["return_date"]
        time_delta = self.current_date - return_date
        days_overdue = time_delta.days
        return days_overdue
    
    
    # bulk add books to inventory from a book dataset (CSV format)
    def parse_CSV(self,filePath,user):
            
        df = pd.read_csv(filePath,usecols=['Title','Author','Genre'])
        data = df.to_numpy()
        for row in data:
            title = row[0]
            author = row[1]
            genre = row[2]
            self.add_item(title, author, genre,user)
        
        print("Parsed CSV and added items to inventory.")
    
    
    # modify the current date recognized by the library instance AND related classes
    # * note that directly changing self.current_date would fail to change the date of related classes such as waitlist
    def set_date(self,new_date,user):
        # authorization check
        if not self.access_control.has_permission(user.username,"set_date"):
            raise PermissionError("Access Denied: set_date")
            
        if not isinstance(new_date,date):
            raise TypeError
        self.current_date = new_date
        
     # testing method
    def clear_all_loans(self,user_manager:UserManager):
        for loan_record in list(self.current_loans.values()):
            book = self.search_by_id(loan_record["item_id"])
            user = user_manager.users[loan_record["user_id"]]
            self.return_item(book, user)
        return len(self.current_loans)==0
    


