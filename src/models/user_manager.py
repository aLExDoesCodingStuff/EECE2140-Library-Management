#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  2 19:45:51 2025

@author: alexmessier
"""
from models.user import User
from auth.access_control import AccessControl
from auth.role import Role

class UserManager:
    
    def __init__(self):
        self.users = {}
        self.next_id = 0
    
    
    def create_user(self, name:str,role:Role,access_control:AccessControl):
        user = User(name,self.next_id)
        self.users[self.next_id] = user
        access_control.assign_role(self.next_id,role)
        self.next_id+=1
        return user
    
    # receives a stored list of users from SaveManager at the start of a session
    def load_users(self,list_of_users):
        for user in list_of_users:
            self.users[user.user_id]=user
            self.next_id = max(self.next_id,user.user_id + 1)
         
    # removes user from user_manager.users. if successful, returns the user
    def delete_user(self,user_id):
        if user_id in self.users:
            user = self.users.pop(user_id)
            return user
        else: return False
        
     # returns a list of users matching a certain username
    def search_users_by_name(self,name:str):
        matches = []
        for user in self.users.values():
            if user.username == name:
                matches.append(user)
        if len(matches)==0:
            print(f">>> No users found with the username: '{name}'.")
            return None
        else: return matches
        
        
        
        