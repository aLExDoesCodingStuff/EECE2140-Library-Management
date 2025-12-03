# models/library.py

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
import pandas as pd
from auth.access_control import AccessControl # Assuming this is available
from models.book import Book


class Library:
    
    def __init__(self, access_control=None):
        self.inventory = []
        self.current_date = date.today()
        self.default_checkout_window = 7 # days
        self.user_id_counter = 0 
        
        if access_control is None:
             self.ac = AccessControl()
        else:
             self.ac = access_control
        
    
    def listInv(self,user):
        # authorization check
        if not self.ac.has_permission(user.username,"list_inv"):
            raise PermissionError("Access Denied: list_inv")
        counter = 1
        for book in self.inventory:
            print(f"{counter}.",book)
            counter+=1
   
    # bulk add books to inventory from a book dataset (CSV format)
    def parse_CSV(self,filePath):
        try:
            print(f"[DEBUG] Attempting to load CSV from: {filePath}")
            df = pd.read_csv(filePath,usecols=['Title','Author','Genre']).dropna()
            data = df.to_numpy()
            for row in data:
                title = row[0]
                author = row[1]
                genre = row[2]
                self.inventory.append(Book(title,author,genre))
            
            print("[DEBUG] Parsed CSV and added items to inventory.")
        
        except Exception as e: # <-- CHANGE TO CATCH A SPECIFIC EXCEPTION
            print(f"[ERROR] Failed to load CSV file.") # <-- ADD THIS LINE
            print(f"[ERROR] The exact error is: {e}")
    
    def __find_available_copy(self,book):
        for copy in book.copies:
            if copy["borrowed_by"] is None:
                return copy
        return None 
    
    def __process_checkout(self, user, book, copy):
        today = self.current_date
        copy["borrowed_by"] = user
        copy["borrow_date"] = today
        copy["return_date"] = today + timedelta(days=self.default_checkout_window)
        user.items_checked_out.append((book, copy))

    def checkout_item(self, book, user):
        if not self.ac.has_permission(user.username,"checkout_item"):
            raise PermissionError("Access Denied: checkout_item")
            
        # Check if book is available on hold
        for (u, window) in list(book.waitlist.holds_pending):
            if u == user: 
                self.__process_checkout(user, book, book.copies[0]) # Assuming first copy for simplicity
                book.waitlist.holds_pending.remove((u, window))
                user.items_on_hold.remove(book)
                return f"{user.username} checked out {book.name} (Hold)."

        # Check for available copy
        copy = self.__find_available_copy(book)
        if copy is not None:
            self.__process_checkout(user, book, copy)
            return f"{user.username} checked out: {book.name} by {book.author}."
        
        # Add to waitlist
        pos = book.waitlist.add_to_queue(user)
        user.items_on_hold.append(book)
        return f"All copies of {book.name} are checked out. {user.username} waitlisted at position {pos}."


    def return_item(self, book, user):
        if not self.ac.has_permission(user.username,"return_item"):
            raise PermissionError("Access Denied: return_item")
            
        copy_found = None
        
        # 1. Find the specific copy the user has checked out
        for book_ref, copy_ref in user.items_checked_out:
            if book_ref == book and copy_ref['borrowed_by'] == user: 
                copy_found = copy_ref
                user.items_checked_out.remove((book_ref, copy_ref))
                break

        if copy_found is None:
            return f"{user.username} does NOT have {book.name} checked out."

        # 2. Reset the copy in the book's inventory
        copy_found["borrowed_by"] = None
        copy_found["borrow_date"] = None
        copy_found["return_date"] = None

        # 3. Advance waitlist if queue is not empty
        if book.waitlist.queue:
            book.waitlist.advance_waitlist()
        
        return f"{user.username} returned {book.name}."
    
    def cleanup_user_data(self, user_obj, admin_user):
        # 1. Authorization check
        if not self.ac.has_permission(admin_user.username, "delete_user"):
            raise PermissionError("Access Denied: delete_user")

        # 2. Handle checked-out items (reset copies and advance waitlist)
        for book_ref, copy_ref in list(user_obj.items_checked_out):
            # Reset the specific copy back to available
            copy_ref["borrowed_by"] = None
            copy_ref["borrow_date"] = None
            copy_ref["return_date"] = None
            
            # Advance waitlist for that book as if it was returned
            if len(book_ref.waitlist.queue) > 0:
                book_ref.waitlist.advance_waitlist()
        
        # 3. Handle waitlist items (remove user from queues/holds)
        for book in self.inventory:
            # Remove from waitlist queue (deque method)
            if user_obj in book.waitlist.queue:
                book.waitlist.queue.remove(user_obj)
            
            # Remove from holds_pending set
            holds_to_remove = set()
            for hold in book.waitlist.holds_pending:
                if hold[0] == user_obj:
                    holds_to_remove.add(hold)
            book.waitlist.holds_pending -= holds_to_remove

        # 4. Clean up AccessControl roles
        if user_obj.username in self.ac.user_roles:
            del self.ac.user_roles[user_obj.username]
            
        return f"Cleaned up {len(user_obj.items_checked_out)}"
    
    # PERSISTENCE METHODS
    
    def catalog_system(self, user, list_of_users):
        if not self.ac.has_permission(user.username,"catalog_system"):
            raise PermissionError("Access Denied: catalog_system")
        master_list_catalog = []
        if list_of_users is None:
            print("No users yet.")
            return master_list_catalog 
            
        for user in list_of_users:
            if user.items_checked_out: 
                for book, copy in user.items_checked_out: 
                    record = {
                        "username": user.username,
                        "book_title": book.name,
                        "return_date": copy["return_date"]
                    }
                    master_list_catalog.append(record)
        return master_list_catalog
        
    def save_state(self, user, master_catalog_list):
        # authorization check
        if not self.ac.has_permission(user.username,"save_state"):
            raise PermissionError("Access Denied: save_state")
            
        output_filename = "catalogSystem.csv"
        master_catalog_df = pd.DataFrame(master_catalog_list)
        if len(master_catalog_df) > 0:
            master_catalog_df.to_csv(output_filename, index=False)
            print(f"\nSuccessfully saved {len(master_catalog_df)} records to {output_filename}.")
        else:
            print("\nNo checked out items to save.")

    # fetches the save-file (CSV) from storage and returns the data as a Pandas dataframe
    @staticmethod
    def load_state(self,filename,user):
        # authorization check
        if not self.ac.has_permission(user.username,"load_state"):
            raise PermissionError("Access Denied: load_state")
        
        try:
            df_catalog = pd.read_csv(filename)
            print(f"\nSuccessfully loaded catalog from {filename} with {len(df_catalog)} records.")
            return df_catalog
        except FileNotFoundError:
            print(f"\n[LOAD ERROR] Catalog file not found: {filename}. Returning an empty catalog DataFrame.")
            return pd.DataFrame()
        except Exception as e:
            print(f"\n[LOAD ERROR] Failed to load catalog: {e}. Returning an empty catalog DataFrame.")
            return pd.DataFrame()
        
#================================================================
 # USER ACCESSIBLE METHODS     

          
    # Checks out a book from the library's inventory. 
    def checkout_item(self,book,user):
        # check if the user has the member role
        if not self.ac.has_permission(user.username,"checkout_item"):
            raise PermissionError("Access Denied: checkout_item")
       
        
        # Check if the user already has the book in their hold list
        if book in user.items_on_hold:
            # if the user has already been through the waitlist (and is finally picking the book up)
            for u,window in book.waitlist.holds_pending:
                if u == user:
                    copy = self.__find_available_copy(book)
                    self.__process_checkout(user,book,copy)
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
        copy = self.__find_available_copy(book)
        if copy != None:
            self.__process_checkout(user,book,copy)
            print(f"{user.username} checked out: {book.name} by {book.author}.") # Update message to include available remaining copies
            return
        
        # if all copies are in use, join the waitlist  
        pos = book.waitlist.add_to_queue(user)
        user.items_on_hold.append(book)
        print(f"All Copies of {book.name} by {book.author} are currently on hold. Added {user.username} to the waitlist (current position: {pos}). ")
    
    # Returns a book to the library's inventory, and assesses late fees if applicable
    def return_item(self,book,user):
        # check authorization
        if not self.ac.has_permission(user.username,"return_item"):
            raise PermissionError("Denied access: return_item")
        
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
        
#================================================================  
# ADMIN ACCESSIBLE METHODS  

    # remove a book from the library's inventory
    def remove_item(self,book,user):
        # authorization check
        if not self.ac.has_permission(user.username,"remove_item"):
            raise PermissionError("Access Denied: remove_item")
        
        if not isinstance(book,Book): raise TypeError
        
        # search for book in library inventory. If found, remove it and return True
        if book in self.inventory:
            self.inventory.remove(book)
            return True
        else: return False
    
    # add a book to the library's inventory
    def add_item(self,book,user):
        # authorization check
        if not self.ac.has_permission(user.username,"add_item"):
            raise PermissionError("Access Denied: add_item")
            
        if not isinstance(book,Book): raise TypeError
        
        # search for book in library inventory. If not found, add it and return True
        if book not in self.inventory:
            self.inventory.append(book)
            return True
        else: return False


    # searches for an available copy of a book. if none found, returns None
    def __find_available_copy(self,book):
        counter = 0
        while counter < len(book.copies):
            if book.copies[counter]["borrowed_by"] == None:
                return book.copies[counter]
            counter+=1
        return None
      
    # tags a book copy with the appropriate information when it is checked out and adds it to the user's checked-out inventory
    def __process_checkout(self,user,book,copy):   
        copy["borrowed_by"] = user
        today = self.current_date
        copy["borrow_date"] = today
        copy["return_date"] = today + timedelta(days=self.default_checkout_window)
        user.items_checked_out.append((book,copy))
    
    
    def check_overdue(self,user):
        # authorization check
        if not self.ac.has_permission(user.username,"check_overdue"):
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
    def parse_CSV(self,filePath):
            
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
    def set_date(self,new_date,user):
        # authorization check
        if not self.ac.has_permission(user.username,"set_date"):
            raise PermissionError("Access Denied: set_date")
            
        if not isinstance(new_date,date):
            raise TypeError
        self.current_date = new_date

    #search for books by exact title 
    def search_by_title(self,title):
        results=[]
        for book in self.inventory:
            if book.name.lower() == title.lower():
                results.append(book)
        if results: 
            print(f"\n{len(results)} found with title '{title}")
            for i, book in enumerate(results,1):
                print(f"{i}. {book.name} by {book.author}, {book.genre}")
        else: 
            print(f"\nNo books found with the title '{title}'")
        return results
        
    #search for books by the exact author name, undercase or uppercase
    def search_by_author(self, author):
        results=[]
        for book in self.inventory: 
            if book.author.lower() == author.lower():
                results.append(book)
        if results: 
            print(f"\n{len(results)} found for author '{author}'")
            for i, book in enumerate(results, 1):
                print(f"{i}. {book.name}, {book.genre})")
        else: 
            print(f"\nNo books found by author '{author}'.")
        return results

    #searches for book by the genre, returns a list of books with that genre
    def search_by_genre(self,genre):
        results=[]
        for book in self.inventory: 
            if book.genre.lower() == genre.lower():
                results.append(book)
        if results: 
            print(f"\n{len(results)} found for genre '{genre}'")
            for i, book in enumerate(results, 1):
                print(f"{i}. {book.name} by {book.author})")
        else: 
            print(f"\nNo books found in genre '{genre}'.")
        return results
   
    def recommend_books(self, user, max_recommendations=5): 
        if not user.checkout_history:
            print(f"\n{user.username} has no checkout history. No recommendations available.")
            return []
        
        favorite_genre = max(user.checkout_history, key=user.checkout_history.get)
        checkout_count = user.checkout_history[favorite_genre]
        
        print(f"\nBased on your checkout history, you've checked out {checkout_count} book(s) in '{favorite_genre}'.")
        print(f"Here are some recommendations from the '{favorite_genre}' genre:\n")
        
        currently_checked_out_books = [book for book, copy in user.items_checked_out] #gets books in that genre
        
        recommendations = []
        for book in self.inventory:
            if book.genre.lower() == favorite_genre.lower() and book not in currently_checked_out_books:
                recommendations.append(book)
        
        if recommendations:
            display_count = min(len(recommendations), max_recommendations)
            for i in range(display_count):
                book = recommendations[i]
                print(f"{i+1}. {book.name} by {book.author}")
        else:
            print(f"No additional books are available in the '{favorite_genre}' genre.")
        
        return recommendations[:max_recommendations]    
           
