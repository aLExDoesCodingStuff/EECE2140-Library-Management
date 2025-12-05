#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from models.waitlist import Waitlist
from models.user import User

class Book:
    
    def __init__(self,name,author,genre,book_id):
        self.name = name
        self.author = author
        self.genre = genre
        self.id = book_id
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
    
    def __eq__(self,other):
        if not isinstance(other,Book):
            return False
        return other.name==self.name and other.author==self.author and other.genre==self.genre
    
        
    