#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 16:18:35 2025

@author: alexmessier
"""



class User: 
    def __init__(self, username:str, user_id:int):
        self.username = username
        self.user_id = user_id
        self.items_checked_out = []
        self.items_on_hold = []
        
    def print_hold_items(self):
        if len(self.items_on_hold)==0:
            print(f"{self.username} does not currently have any books on hold.")
        else:
            counter = 0
            for book in self.items_on_hold:
                print(f"{counter}. {book}")
    
    def print_checked_out(self,user):
        if len(self.items_checked_out)==0:
            print(f"{self.username} does not currently have any books on hold")
        else: 
            counter = 0
            for book,loan_number in self.items_checked_out:
                print(f"{counter}. Loan No.{loan_number}. Book: {book}.")
                counter +=1
                
    def __str__(self):
        return self.username
    
    def __repr__(self):
        return f"username ='{self.username}',user_id='{self.user_id}',items_checked_out={self.items_checked_out},items_on_hold={self.items_on_hold}"
        
