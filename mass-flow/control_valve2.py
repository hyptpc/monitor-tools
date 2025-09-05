#!/usr/bin/env python3

import datetime
# import epics
import html
import json
import logging
import os
# import requests
import subprocess
import time

# import pmx_a

mqv0002 = '/home/oper/share/monitor-tools/mass-flow/flow2.py'

monitor_threshold = [40, 80]
alarm_threshold = [0, 150]
dplimit = 5.0 # [Pa]
vstep = 0.005 # [V]
voffset = 0.002 # [V]
vlimit = [0, 10]
monitor_interval = 20 # [s]
alarm_interval = 600 # [s]

delta_flow = 10

webhook_url = ('https://hooks.slack.com/services/'
               + 'TFNR5RW9Z/BG5F2C8M7/IKjfTYk2x1Kei7JKiswYmUJg')
channel = '#alarm'
bot_name = 'incoming-webhook'
tpc_url = 'http://www-online.kek.jp/~sks/e42/hyptpc/'


#______________________________________________________________________________
def get_difp():
  try:
    command = ['curl',
               'http://logger2.monitor.k18br/digital.cgi?chg=0']
    output_str = subprocess.run(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE).stdout.decode()
    for line in output_str.splitlines():
      if 'CH 2<' in line:
        line = line.replace('&nbsp;', '').replace(' ', '')
        dp = line.split('<b>')[2].split('</b>')[0]
        if dp == '+++++++':
          dp = 9999
#        print('test  dp= ', dp )
        return float(dp)
    # with open("/home/sks/work/hyptpc/dp.txt") as f:
    #   return float(f.read())
  except:
    return -9999

#______________________________________________________________________________
def get_flow():
  try:
    # command = ['/home/sks/monitor-tools/MQV9500/mqv0002.py']
    command = [mqv0002]
    output_str = subprocess.run(command, stdout=subprocess.PIPE).stdout.decode()
    for line in output_str.splitlines():
      if 'FlowMon' in line:
        return float(line.split()[2])*1000
    # with open("/home/sks/work/hyptpc/flow.txt") as f:
    #   return float(f.read())*1000
  except:
    return -9999

#______________________________________________________________________________
def control_valve():
  # pmxa = pmx_a.PMX_A('kikusui1', timeout=1.0, debug=False)
  # pmxa.idn()
  prev_p = None
  prev_ok = True
  prev_time = 0
  try:
    while True:
      now = str(datetime.datetime.now())[:19]
      now2 = str(datetime.datetime.now())[:10]
      flow = get_flow()
      f = open(f'data/{now2}.txt','a')
      f.write(f'{now} {flow:5.0f}\n') 
      f.close()
      pressure = get_difp()
 
 #     print('test2  pressure= ', pressure )  
      if pressure is None or pressure == -9999:
        time.sleep(1)
        continue
      if prev_p is not None:
        dp = pressure - prev_p
      else:
        dp = 0
        
 
      prev_p = pressure
      monitor_status = monitor_threshold[0] < pressure and pressure < monitor_threshold[1]
      valve_status = 'Stay'
      prev_f = flow
      # if not monitor_status:
      if (pressure <= monitor_threshold[0] and dp < 5) or dp < -10:
        valve_status = 'flow up'
        flow = flow - delta_flow
      elif (pressure  == 9999):
        valve_status = 'flow down fast'
        flow = flow + 100
      elif (monitor_threshold[1] <= pressure and dp > -5) or dp > 10:
        valve_status = 'flow down'
        flow = flow + delta_flow
      print(f'{now}  F={flow:5.0f}({flow-prev_f:6.0f})  ' +
            f'P={pressure:>7.1f}  dP={dp:>5.1f}  '+
            f'Stat={valve_status}')
      if flow != prev_f:
        command=f'{mqv0002} {flow:.0f}'
        os.system(command)
      # alarm_status = alarm_threshold[0] < pressure and pressure < alarm_threshold[1]
      # if alarm_status:
      #   send_alarm = False
      # else:
      #   if prev_ok or (alarm_interval < time.time() - prev_time):
      #     send_alarm = True
      #     message = f'Received TPC pressure alarm : {pressure:.1f} Pa.'
      #     web_message = f'Check {tpc_url}'
      #     payload = {
      #       'channel': channel,
      #       'username': bot_name,
      #       'text': message,
      #       'attachments': [{
      #         'color': '#000000',
      #         'fallback': message,
      #         'text': web_message,
      #       }]
      #     }
      #     # requests.post(webhook_url, data=json.dumps(payload))
      #     prev_time = time.time()
      #   else:
      #     send_alarm = False
      prev_ok = monitor_status
      # if pressure > 300 and epics.caget('GAS:TPC:FSET') > 50:
      #   print('Decrease gas flow for safety')
      #   os.system('/home/sks/monitor-tools/MQV9500/mqv9500.py 50')
      time.sleep(monitor_interval)
  except KeyboardInterrupt:
    print()

if __name__ == '__main__':
  control_valve()
  # print(get_difp())
