#!/usr/bin/env python3
import time
from panda import Panda

class Buttons:
    NONE = 0
    RES_ACCEL = 1
    SET_DECEL = 2
    GAP_DIST = 3
    CANCEL = 4

def main():
    panda = Panda()
    panda.set_safety_mode(Panda.SAFETY_ALLOUTPUT)
    
    send_can_id = 0x4F1  # CAN ID to send messages
    send_can_data = b"\x00\x00\x00\x00\x00\x00\x00\x00"  # Dummy data set to all zeros
    send_can_bus = 0  # Sending CAN bus index
    receive_can_bus = 0  # Receiving CAN bus index
    last_send_time = time.time()
    sending_enabled = False  # Variable to control whether messages are sent

    while True:
        # Check for user input to toggle sending or exit
        if sending_enabled:
            current_time = time.time()
            # Send a dummy message every second on bus 0
            if current_time - last_send_time >= 1.0:
                panda.can_send(send_can_id, send_can_data, send_can_bus)
                print(f"Sent message {send_can_data.hex()} on CAN ID {hex(send_can_id)} to bus {send_can_bus}")
                last_send_time = current_time

        # Check for new messages on bus 1 and modify them
        messages = panda.can_recv()
        for address, _, data, src in messages:
            if src == receive_can_bus and address == send_can_id:
                print(f"Received message {data.hex()} on CAN ID {hex(address)} from bus {src}")
                # Simulate unpacking and modifying CAN data
                can_data = list(data)  # Convert bytes to list of integers for manipulation
                can_data[0] = Buttons.RES_ACCEL  # Modify the button state directly in the data list
                modified_data = bytes(can_data)  # Convert list back to bytes
                panda.can_send(address, modified_data, receive_can_bus)
                print(f"Modified and sent message {modified_data.hex()} on CAN ID {hex(address)} to bus {receive_can_bus}")

        # Brief sleep to prevent overwhelming the CPU
        time.sleep(0.01)

if __name__ == "__main__":
    main()
