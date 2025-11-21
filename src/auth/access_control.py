#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  3 15:47:35 2025

@author: alexmessier
"""

import sys
from pathlib import Path
from auth.role import Role


class AccessControl:
    def __init__(self):
        self.user_roles = {}  # maps user_id → list of roles

    # assign a role or list of roles to a user
    def assign_role(self, user_id, role):
        # make sure role is a Role or list of Roles
        if not isinstance(role,Role) and not isinstance(role,list):
            return False
        
        if type(role)==Role:
            self.user_roles.setdefault(user_id,set()).add(role)
            return self.user_roles[user_id]
        else:
            for r in role:
                self.user_roles.setdefault(user_id,set()).add(r)
            return self.user_roles[user_id]

    def has_permission(self, user_id, permission):
        if user_id in self.user_roles.keys():
            for role in self.user_roles[user_id]:
                for p in role.permissions:
                    if p == permission:
                        return True
        else: return False
                
    
    def requires_permission(permission):
        def decorator(func):
            def wrapper(self, user, *args, **kwargs):
                # self must have a reference to AccessControl (e.g., self.ac)
                if not self.ac.has_permission(user, permission):
                    raise PermissionError(f"Access denied: {permission}")
                return func(self, user, *args, **kwargs)
            return wrapper
        return decorator
    


