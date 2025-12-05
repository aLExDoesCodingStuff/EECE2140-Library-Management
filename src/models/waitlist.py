#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 16:18:08 2025

@author: alexmessier
"""

from collections import deque
from datetime import timedelta
from datetime import date

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
        if len(self.queue)>0:
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

    
            