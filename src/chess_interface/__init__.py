#!/usr/bin/env python

"""
Library for UCI chess engine communication.
"""
import os
import sys

__all__ = ['UCI']
from .main import UCI

PROJECT_PATH = os.getcwd()
sys.path.append(PROJECT_PATH)
