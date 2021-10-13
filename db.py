# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', passwd='123456789', db='web')

cursor = conn.cursor()

