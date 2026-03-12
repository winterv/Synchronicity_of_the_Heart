import socket
import json
import time
import config

# WLED device details
WLED_IP = config.UDP_IP  # Replace with your WLED device's IP address
WLED_UDP_PORT = config.UDP_PORT      # Default WLED sync port

def send_wled_command_udp(ip, port, command):
    """
    Sends a JSON command to a WLED device over UDP.
    """
    try:
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Serialize the JSON command to bytes
        message = json.dumps(command).encode('utf-8')
        
        # Send the message
        sock.sendto(message, (ip, port))
        print(f"Sent command: {message.decode('utf-8')}")
        
    except socket.error as e:
        print(f"Socket error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        sock.close()

# Example usage:
# Command to set the effect (fx) to "Chase" (ID might be different, check documentation) 
# and set the primary color (col) to red.

# Note: Effect IDs can vary. Let's assume 'FX=2' is the ID for the "Chase" effect for this example.
# You need to verify the exact ID for the effect you want to use in your WLED version.
for speed in range(125,255,10):
    Red = speed
    Green = 0
    Blue = 125-speed/2
    command_to_send = {
        "seg": [
            {
                "fx": 227,  # The ID of the effect/pattern
                "col": [[0, 255, 0],[Red,Green,Blue],(0,255,0)], # Primary color: Red (R, G, B)
                "pal": 63,
                "sx": speed,
                "ix": 28,
            }
        ]
    }

    send_wled_command_udp(WLED_IP, WLED_UDP_PORT, command_to_send)
    time.sleep(2)

for speed in range(125,255,10):
    Red = speed
    Green = 0
    Blue = 125-speed/2
    
    command_to_send = {
        "seg": [
            {
                "fx": 223,  # The ID of the effect/pattern
                "col": [[0, 255, 0],[Red,Green,Blue],(0,255,0)], # Primary color: Red (R, G, B)
                "pal": 63,
                "sx": speed,
                "ix": 28,
            }
        ]
    }

    send_wled_command_udp(WLED_IP, WLED_UDP_PORT, command_to_send)
    time.sleep(2)

# Command to set the effect to "Solid" (ID is typically 0)
# time.sleep(3) # Wait a few seconds to see the first effect

# solid_color_command = {
#     "seg": [
#         {
#             "fx": 0,  # Effect ID 0 is usually "Solid"
#             "col": [[0, 255, 0]] # Primary color: Green
#         }
#     ]
# }

# send_wled_command_udp(WLED_IP, WLED_UDP_PORT, solid_color_command)

pass