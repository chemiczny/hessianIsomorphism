#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 20 10:38:00 2019

@author: michal
"""


def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

def isint(value):
  try:
    int(value)
    return True
  except ValueError:
    return False