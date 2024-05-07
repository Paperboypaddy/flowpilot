#!/usr/bin/env python3
import os
import time
from panda import Panda

class Buttons:
    NONE = 0
    RES_ACCEL = 1
    SET_DECEL = 2
    GAP_DIST = 3
    CANCEL = 4

def modify_cruise_control_state(panda, can_id, can_data):
    # Modify the cruise control button state to RES_ACCEL
    can_data["CF_Clu_CruiseSwState"] = Buttons.RES_ACCEL
    # Pack and send the modified message back to the CAN bus
    panda.can_send(can_id, panda.can_pack(can_data), 0)

def capture_and_modify_messages():
    panda = Panda(serial='44003d000c51363338383037')
    panda.set_safety_mode(Panda.SAFETY_ALLOUTPUT)
    canbus = int(os.getenv("CAN", "0"))  # Default to CAN bus 0

    while True:
        messages = panda.can_recv()
        for address, _, data, src in messages:
            if src == canbus and address == 0x4F1:  # Assuming 0x4F1 is the CAN ID for CLU11
                can_data = panda.can_unpack(data)
                if "CF_Clu_CruiseSwState" in can_data:
                    modify_cruise_control_state(panda, address, can_data)

        time.sleep(0.01)  # Sleep to prevent excessive CPU usage

if __name__ == "__main__":
    capture_and_modify_messages()
