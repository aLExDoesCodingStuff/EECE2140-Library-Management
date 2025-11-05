#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  3 15:47:35 2025

@author: alexmessier
"""

class AccessControl:
    def __init__(self):
        self.user_roles = {}  # maps user_id → list of roles

    def assign_role(self, user, role):
        self.user_roles.setdefault(user, set()).add(role)

    def has_permission(self, user, permission):
        roles = self.user_roles.get(user, set())
        return any(permission in role.permissions for role in roles)

    def requires_permission(permission):
        def decorator(func):
            def wrapper(self, user, *args, **kwargs):
                # self must have a reference to AccessControl (e.g., self.ac)
                if not self.ac.has_permission(user, permission):
                    raise PermissionError(f"Access denied: {permission}")
                return func(self, user, *args, **kwargs)
            return wrapper
        return decorator
