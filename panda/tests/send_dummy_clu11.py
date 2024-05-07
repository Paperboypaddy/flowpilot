#!/usr/bin/env python3
import time
from panda import Panda

def send_and_receive_messages():
    panda = Panda(serial='3e003c000c51363338383037')
    panda.set_safety_mode(Panda.SAFETY_ALLOUTPUT)
    send_can_id = 0x4F1  # Example CAN ID to send messages
    send_can_data = b"\x00\x00\x00\x00\x00\x00\x00\x00"  # Dummy data set to all zeros
    send_can_bus = 0  # Sending CAN bus index
    receive_can_bus = 1  # Receiving CAN bus index
    last_send_time = time.time()

    while True:
        current_time = time.time()

        # Send a dummy message every second
        if current_time - last_send_time >= 1.0:
            panda.can_send(send_can_id, send_can_data, send_can_bus)
            print(f"Sent message {send_can_data.hex()} on CAN ID {hex(send_can_id)}")
            last_send_time = current_time

        # Check for new messages and process them immediately
        messages = panda.can_recv()
        for address, _, data, src in messages:
            if src == receive_can_bus:
                print(f"Received message {data.hex()} on CAN ID {hex(address)} from bus {src}")

        # Brief sleep to prevent overwhelming the CPU
        time.sleep(0.01)

if __name__ == "__main__":
    send_and_receive_messages()