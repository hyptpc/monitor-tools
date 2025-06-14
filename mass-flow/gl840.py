#!/usr/bin/env python3

import datetime
import json
import logging
import html.parser
import requests
import time

#______________________________________________________________________________
class GL840(html.parser.HTMLParser):
  ipaddress = 'logger2.monitor.k18br'
  data_dict = dict()
  ch = None
  val = None
  unit = None

  #____________________________________________________________________________
  def handle_data(self, data):
    data = data.strip().replace(' ', '').replace('+', '')
    if len(data) == 0:
      return
    try:
      float(data)
    except ValueError:
      if 'CH' in data:
        self.ch = int(data[2:])
        self.val = None
        self.unit = None
      else:
        self.unit = data
    else:
      self.val = float(data)
    if (self.ch is not None and
        self.val is not None and
        self.unit is not None):
      self.data_dict[self.ch] = (self.val, self.unit)
      # print(f'Found data: ch={self.ch} '+
      #       f'{self.data_dict[self.ch]}')

  #____________________________________________________________________________
  def get_data(self, ch):
    if ch in self.data_dict:
      return self.data_dict[ch]
    else:
      return None

  #____________________________________________________________________________
  def parse(self):
    try:
      ret = requests.get(f'http://{self.ipaddress}/digital.cgi?chg=0')
      self.feed(ret.text)
    except:
      pass

#______________________________________________________________________________
if __name__ == '__main__':
  gl840 = GL840()
  gl840.parse()
  print(gl840.get_data(2))
