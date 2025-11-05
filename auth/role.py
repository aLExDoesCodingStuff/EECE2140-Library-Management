#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  3 15:45:09 2025

@author: alexmessier
"""

class Role: 
    def __init__(self,name,permissions):
        self.name = name
        self.permissions = set(permissions)
        
    def __repr__(self):
        return self.name
        