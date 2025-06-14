#!/usr/bin/env python3

import argparse
import socket

'''
  Mass flow controller MQV0002
'''

default_host = '192.168.20.14'
default_port = 4001
default_addr = 1

#______________________________________________________________________________
class MQV0002():
  ''' class MQV0002. '''
  STX = b'\x02'
  ETX = b'\x03'
  TERM = b'\r\n'
  SUBADDR = b'00'
  DEVICECODE = b'X'
  YELLOW = '\033[33;1m'
  END = '\033[0m'

  #____________________________________________________________________________
  def __init__(self, host, port, addr, timeout=10.0):
    ''' initialize settings and open socket. '''
    self.host = host
    self.port = port
    self.addr = addr
    self.status = True
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('host = {}, port = {}, addr = {}'.format(host, port, addr))
    self.sock.settimeout(timeout)
    try:
      self.sock.connect((self.host, self.port))
      self.is_open = True
      print('connected')
    except (socket.error, socket.timeout):
      self.is_open = False
      print('failed')
      return

  #____________________________________________________________________________
  def __del__(self):
    ''' close socket. '''
    if self.is_open:
      self.sock.close()

  #____________________________________________________________________________
  def __apply(self, command):
    ''' apply command. '''
    if not self.is_open:
      return
    data = (self.STX + '{:02d}'.format(self.addr).encode('utf-8')
            + self.SUBADDR + self.DEVICECODE + command + self.ETX)
    data += self.__cplsum(data, len(data)) + self.TERM
    print('apply command "{}"'.format(command.decode('utf-8')), end='')
    self.sock.send(data)
    buf = bytes()
    while True:
      c = self.sock.recv(1)
      buf += c
      if self.TERM in buf:
        break
    cpos = len(buf) - len(self.TERM) -2
    csum = self.__cplsum(buf, cpos)
    print(' -> "{}"'.format(buf[6:-5].decode('utf-8')))
    if buf[cpos:-2] != csum:
      print(self.YELLOW + 'Checksum is wrong' + self.END)
      self.status = False
    buf = buf[6:-5].decode('utf-8')
    ret = int(buf[0:2])
    if ret != 0:
      print(self.YELLOW + 'Error code is returned : ' + str(ret) + self.END)
      self.status = False
    return ret, buf[3:].split(',')

  #____________________________________________________________________________
  def __cplsum(self, message, length):
    ''' calculate CPL sum. '''
    num = 0
    for i in range(length):
      num += message[i]
    num = (( - (num & 0x000000FF) ) & 0x000000FF)
    num = '{:02X}'.format(num)
    return num.encode('utf-8')

  #____________________________________________________________________________
  def __read(self, addr, size):
    ''' read data. '''
    command = 'RS,{:d}W,{:d}'.format(addr, size).encode('utf-8')
    ret, data = self.__apply(command)
    if ret == 0 and len(data) == size:
      return data
    else:
      return self.__read(addr, size)

  #____________________________________________________________________________
  def __write(self, addr, wdata):
    ''' write data. '''
    command = 'WS,{:d}W,{:d}'.format(addr, wdata).encode('utf-8')
    ret, data = self.__apply(command)
    if ret == 0:
      if len(data) == 1 and len(data[0]) == 0:
        return data
      else:
        print('retry')
        return self.__write(addr, wdata)
    else:
      return None

  #____________________________________________________________________________
  def info(self):
    ''' print data. '''
    # 1000
    data = self.__read(1001, 6)
    if int(data[0]) == 0:
      gas_type = 'User'
    elif int(data[0]) == 1:
      gas_type = 'N2/Air'
    elif int(data[0]) == 2:
      gas_type = 'O2'
    elif int(data[0]) == 3:
      gas_type = 'Ar'
    elif int(data[0]) == 4:
      gas_type = 'CO2'
    elif int(data[0]) == 5:
      gas_type = 'Town gas 1'
    elif int(data[0]) == 6:
      gas_type = 'C3H8'
    elif int(data[0]) == 7:
      gas_type = 'CH4'
    elif int(data[0]) == 8:
      gas_type = 'C4H10'
    elif int(data[0]) == 9:
      gas_type = 'H2'
    elif int(data[0]) == 10:
      gas_type = 'He'
    elif int(data[0]) == 11:
      gas_type = 'Town gas 2'
    else:
      gas_type = 'Unknown'
    full_scale = float(data[1])
    scale_mon = (10**(-int(data[2])+1))
    scale_int = (10**(-int(data[3])+1))
    if int(data[4]) == 0:
      unit_mon = 'mL/min'
    elif int(data[4]) == 1:
      unit_mon = 'L/min'
    else:
      unit_mon = 'Unknown'
    if int(data[5]) == 1:
      unit_int = 'L'
    elif int(data[5]) == 2:
      unit_int = 'm3'
    else:
      unit_int = 'Unknown'
    # 1200
    data = self.__read(1201, 8)
    alarm_status = int(data[0])
    ctrl_status = int(data[2])
    if ctrl_status&1 == 0:
      ctrl_status = 'OFF'
    else:
      ctrl_status = 'ON'
    valve = int(data[3])
    if valve == 0:
      valve = 'Close'
    elif valve == 1:
      valve = 'Cntrolled'
    elif valve == 2:
      valve = 'Full Open'
    sp = int(data[4])
    fset = float(data[5])*scale_mon
    fmon = float(data[6])*scale_mon
    vcur = float(data[7])*0.1
    # 1600
    data = self.__read(1601, 4)
    iset = (int(data[0]) + int(data[1])*(10**4))*scale_int
    imon = (int(data[2]) + int(data[3])*(10**4))*scale_int
    # 2019
    data = self.__read(2019, 1)
    if int(data[0]) == 0:
      ref = '20 degC, 101.325 kPa'
    elif int(data[0]) == 1:
      ref = '0 degC, 101.325 kPa'
    elif int(data[0]) == 2:
      ref = '25 degC, 101.325 kPa'
    elif int(data[0]) == 3:
      ref = '35 degC, 101.325 kPa'
    print('='*79)
    print('GasType   = {}\nFullScale = {:.3f} {}\nStatus    = {}'
          .format(gas_type, full_scale*scale_mon, unit_mon,
                  ctrl_status))
    print('Valve     = {}\nSP        = {}\nFlowSet   = {:.3f} {}'
          .format(valve, sp, fset, unit_mon))
    print('FlowMon   = {:.3f} {}\nValveCurr = {:.1f} %'
          .format(fmon, unit_mon, vcur))
    # print('IntSet    = {:9.2f} {}'.format(iset, unit_int))
    # print('IntMon    = {:9.2f} {}'.format(imon, unit_int))
    print('TotalMon  = {:.2f} {}'.format(imon, unit_int))
    print('Reference = {}'.format(ref))
    if alarm_status != 0:
      print(self.YELLOW, end='')
    print('AlarmBit  = {}'.format(format(alarm_status, '012b')))
    print(self.END, end='')
    print('='*79)

  #____________________________________________________________________________
  def reset_int(self):
    ''' reset integrated volume. '''
    self.__write(1603, 0)
    self.__write(1604, 0)
    self.__write(4603, 0)
    self.__write(4604, 0)

  #____________________________________________________________________________
  def init(self):
    ''' initialize. '''
    self.__write(5018, 3)
    self.__write(5019, 2)

  #____________________________________________________________________________
  def run(self, val):
    ''' run command. '''
    self.status = True
    if len(val) == 0 or val == 'info':
      self.info()
    elif val == 'on':
      self.valve_on()
    elif val == 'off':
      self.valve_off()
    elif val == 'reset':
      self.reset_int()
    elif val == 'init':
      self.init()
    else:
      try:
        self.set_flow(int(int(val)/10))
      except ValueError:
        print(self.YELLOW + 'Invalid argument : ' + val + self.END)
        self.status = False
    if self.status:
      print('Successfully done')

  #____________________________________________________________________________
  def set_flow(self, val):
    ''' set flow '''
    self.__write(1401, val)

  #____________________________________________________________________________
  def valve_off(self):
    ''' valve off '''
    self.__write(1204, 0)

  #____________________________________________________________________________
  def valve_on(self):
    ''' valve on '''
    self.__write(1204, 1)

#______________________________________________________________________________
if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--host', default=default_host,
                      help=('IP address of serial device server ' +
                            f'(default={default_host})'))
  parser.add_argument('--port', default=default_port, type=int,
                      help=('Port number of serial device server ' +
                            f'(default={default_port})'))
  parser.add_argument('--addr', default=default_addr, type=int,
                      help='Device address of MQV0002 ' +
                      f'(default={default_addr})')
  parser.add_argument('arg', default='', nargs='?',
                      help='"on" = valve on, ' +
                      '"off" = valve off, ' +
                      '"reset" = reset integrated gas volume, ' +
                      '"(int)" = set flow, ' +
                      '')
  parsed, unparsed = parser.parse_known_args()
  mqv = MQV0002(host=parsed.host, port=parsed.port, addr=parsed.addr)
  if mqv.is_open:
    mqv.run(parsed.arg)
