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
        books_added = 0 
        try:
            print(f"[DEBUG] Attempting to load CSV from: {filePath}")
            df = pd.read_csv(filePath,usecols=['Title','Author','Genre']).dropna()
            
            print(f"[DEBUG] CSV read successful. Found {len(df)} rows.")
            
            data = df.to_numpy()
            
            for row in data:
                title = row[0]
                author = row[1]
                genre = row[2]
                
                try:
                    self.inventory.append(Book(title,author,genre))
                    books_added += 1
                except Exception as book_err:
                    print(f"[ERROR] Failed to instantiate Book for: {title} by {author}. Error: {book_err}. Skipping this row.")
                    # Continue to try next row if only a few fail
                    pass 

            
            print(f"[DEBUG] Parsed CSV and added {books_added} items to inventory.")
            return books_added
        
        except FileNotFoundError:
            # Added specific print for File Not Found
            print(f"[ERROR] Failed to load CSV file. File not found at {filePath}.")
            return 0
        except Exception as e:
            print(f"[ERROR] Failed to load or process CSV file.") 
            print(f"[ERROR] The exact error is: {e}")
            return 0
    
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
        pass 


    def return_item(self, book, user):
        pass

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
    def checkout_item(self, book, user):
    
    # 1. Permission check
        if not self.ac.has_permission(user.username, "checkout_item"):
            raise PermissionError("Access Denied: checkout_item")
    
    # Define concise history update function
        def _update_history(book, user):
            genre_name = book.genre.strip()
            user.checkout_history[genre_name] = user.checkout_history.get(genre_name, 0) + 1
    
        # 2. Check for Hold/Waitlist Pickup
        if book in user.items_on_hold:
            for u, window in book.waitlist.holds_pending:
                if u == user:
                    copy = self.__find_available_copy(book)
                    self.__process_checkout(user, book, copy)
                
                    _update_history(book, user) 
                
                    return f"Checkout successful (Hold): {book.name}"
        
            # User is on hold but not currently in the pending pickup window
            raise Exception(f"{book.name} is already on hold (position: {book.waitlist.get_pos(user)})")
        
        # Check for immediate availability
        copy = self.__find_available_copy(book)
        if copy is not None:
            self.__process_checkout(user, book, copy)
            
            _update_history(book, user) # <HISTORY UPDATE (Initial Checkout)
            
            return f"Checkout successful: {book.name}"
            
        # If not available, join the waitlist
        
        
        pos = book.waitlist.add_to_queue(user)
        user.items_on_hold.append(book)
        raise Exception(f"All copies checked out. Added to waitlist (position: {pos})")
        
        
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
            # print(f"{user} does not currently have {book.name} checked out.") # Removed print for UI
            raise Exception(f"{book.name} is NOT checked out by you.")
            
        
        # clear the update the copy information on the book
        copy["borrowed_by"] = None
        copy["borrow_date"] = None
        copy["return_date"] = None
        
        # remove the book from user's items_checked_out list
        for b,c in user.items_checked_out:
            if b == book:
                user.items_checked_out.remove((b,c))
                break
        
        
        # advance the waitlist
        book.waitlist.advance_waitlist()    
        return f"Return successful: {book.name}"
        
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
            
        overdue_list = []
        for book in self.inventory:
            overdue = self.__get_overdue_copies(book)
            for copy in overdue:
                overdue_list.append(copy)
        return overdue_list
         
    # checks a book object for checked-out copies which are overdue
    # returns a list of overdue copies
    def __get_overdue_copies(self,book):
        
        if not isinstance(book,Book):
            raise TypeError
        
        overdue_copies = []
        for copy in book.copies:
            # see if copy is checked out
            if copy["borrowed_by"]!=None:
                # Use strict inequality for 'overdue' to align with UI logic
                if copy["return_date"] < self.current_date: 
                    overdue_copies.append(copy)
        return overdue_copies


    def __get_days_overdue(self,copy):
        return_date = copy["return_date"]
        time_delta = self.current_date - return_date
        days_overdue = time_delta.days
        return days_overdue
    
    # modify the current date recognized by the library instance AND related classes
    def set_date(self,new_date,user):
        # authorization check
        if not self.ac.has_permission(user.username,"set_date"):
            raise PermissionError("Access Denied: set_date")
            
        if not isinstance(new_date,date):
            raise TypeError
        self.current_date = new_date


    #search for books by title 
    def __search_by_substring(self, search_term, field):
        """Helper for case-insensitive substring search."""
        results = []
        term_lower = search_term.lower()
        
        for book in self.inventory:
            try:
                if field == 'title' and term_lower in book.name.lower():
                    results.append(book)
                elif field == 'author' and term_lower in book.author.lower():
                    results.append(book)
                elif field == 'genre' and term_lower in book.genre.lower():
                    results.append(book)
            except AttributeError:
                # Handles cases where the book object might be missing the attribute
                continue 
                
        if results: 
            # Output for console/terminal
            print(f"\n{len(results)} found for '{search_term}' in field '{field}'.")
        else: 
            print(f"\nNo books found matching '{search_term}' in field '{field}'.")
            
        return results

    #search for books by title
    def search_by_title(self,title):
        return self.__search_by_substring(title, 'title')
        
    #search for books by the author name
    def search_by_author(self, author):
        return self.__search_by_substring(author, 'author')

    #searches for book by the genre, returns a list of books with that genre
    def search_by_genre(self,genre):
        return self.__search_by_substring(genre, 'genre')
    
    def search_catalog(self, search_term, search_by):
        """
        Delegates search to the appropriate specific function based on search_by.
        """
        search_by = search_by.lower()
        if search_by == 'title':
            return self.search_by_title(search_term)
        elif search_by == 'author':
            return self.search_by_author(search_term)
        elif search_by == 'genre':
            return self.search_by_genre(search_term)
        else:
            print(f"[ERROR] Invalid search category: {search_by}")
            return []
        
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
