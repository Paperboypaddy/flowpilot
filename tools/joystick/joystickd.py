#!/usr/bin/env python
# hardforked from https://github.com/commaai/openpilot/blob/1d8fc4d21caf55368209b7bbafa34327962a6a97/tools/joystick/joystickd.py
import os
import argparse
import threading
from evdev import InputDevice, categorize, ecodes

import cereal.messaging as messaging
from common.realtime import Ratekeeper
from common.numpy_fast import interp, clip
from common.params import Params
from tools.lib.kbhit import KBHit


class Keyboard:
  def __init__(self):
    self.kb = KBHit()
    self.axis_increment = 0.05  # 5% of full actuation each key press
    self.axes_map = {'w': 'gb', 's': 'gb',
                     'a': 'steer', 'd': 'steer'}
    self.axes_values = {'gb': 0., 'steer': 0.}
    self.axes_order = ['gb', 'steer']
    self.cancel = False
    self.set = False

  def update(self):
    key = self.kb.getch().lower()
    self.cancel = False
    if key == 'r':
      self.axes_values = {ax: 0. for ax in self.axes_values}
    elif key == 'c':
      self.cancel = True
    elif key in self.axes_map:
      axis = self.axes_map[key]
      incr = self.axis_increment if key in ['w', 'a'] else -self.axis_increment
      self.axes_values[axis] = clip(self.axes_values[axis] + incr, -1, 1)
    else:
      return False
    return True


class Joystick:
    def __init__(self, device_path="/dev/input/event13"):
        self.device = InputDevice(device_path)
        self.cancel_button = 'BTN_NORTH'
        self.set_button = 'BTN_SOUTH'
        
        # Define axes for steering and acceleration
        accel_axis = 'ABS_Y'
        steer_axis = 'ABS_Z'
        
        self.min_axis_value = {accel_axis: 0., steer_axis: 0.}
        self.max_axis_value = {accel_axis: 255., steer_axis: 255.}
        self.axes_values = {accel_axis: 0., steer_axis: 0.}
        self.axes_order = [accel_axis, steer_axis]
        self.cancel = False
        self.set = False

    def update(self):
        for event in self.device.read_loop():  # Use read_loop instead of read
            if event.type == ecodes.EV_ABS:  # Handle axis events
                axis = ecodes.ABS[event.code]
                
                if axis == 'ABS_Y':
                    # Normalize the value between -1 and 1
                    norm = -interp(event.value, [self.min_axis_value[axis], self.max_axis_value[axis]], [-1., 1.])
                    self.axes_values[axis] = norm if abs(norm) > 0.05 else 0.  # Apply deadzone
                elif axis == 'ABS_Z':
                    # Normalize the value between -1 and 1
                    norm = -interp(event.value, [self.min_axis_value[axis], self.max_axis_value[axis]], [-1., 1.])
                    self.axes_values[axis] = norm if abs(norm) > 0.05 else 0.  # Apply deadzone

            # Check for button press/release events
            if event.type == ecodes.EV_KEY:
                if event.code == self.cancel_button and event.value == 1:
                    self.cancel = True
                elif event.code == self.set_button and event.value == 1:
                    self.set = not self.set
        return True



def send_thread(joystick):
  joystick_sock = messaging.pub_sock('testJoystick')
  rk = Ratekeeper(100, print_delay_threshold=None)
  while 1:
    dat = messaging.new_message('testJoystick')
    dat.testJoystick.axes = [joystick.axes_values[a] for a in joystick.axes_order]
    dat.testJoystick.buttons = [joystick.cancel, joystick.set]
    joystick_sock.send(dat.to_bytes())
    print('\n' + ', '.join(f'{name}: {round(v, 3)}' for name, v in joystick.axes_values.items()))
    if "WEB" in os.environ:
      import requests
      requests.get("http://"+os.environ["WEB"]+":5000/control/%f/%f" % tuple([joystick.axes_values[a] for a in joystick.axes_order][::-1]), timeout=None)
    rk.keep_time()

def joystick_thread(joystick):
  Params().put_bool('JoystickDebugMode', True)
  threading.Thread(target=send_thread, args=(joystick,), daemon=True).start()
  while True:
    joystick.update()

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Publishes events from your joystick to control your car.\n' +
                                               'flowpilot must be offroad before starting joysticked.',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('--keyboard', action='store_true', help='Use your keyboard instead of a joystick')
  parser.add_argument('--gamepad', action='store_true', help='Use gamepad configuration instead of joystick')
  args = parser.parse_args()

  if not Params().get_bool("IsOffroad"):
    print("The car must be off before running joystickd.")
    exit()

  print()
  if args.keyboard:
    print('Gas/brake control: `W` and `S` keys')
    print('Steering control: `A` and `D` keys')
    print('Buttons')
    print('- `R`: Resets axes')
    print('- `C`: Cancel cruise control')
  else:
    print('Using joystick.')

  joystick = Keyboard() if args.keyboard else Joystick("/dev/input/event13")
  joystick_thread(joystick)