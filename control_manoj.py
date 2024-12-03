import socket
from pynput import keyboard

# ESP32 server configuration
ESP32_IP = "192.168.4.1"  # Replace with your ESP32 IP address
ESP32_PORT = 80

# Key mappings
COMMANDS = {
    "s": "MOVE_FORWARD",
    "w": "MOVE_BACKWARD",
    "d": "TURN_LEFT",
    "a": "TURN_RIGHT",
    "c": "STOP",
}


# Create a socket connection to ESP32
def connect_to_esp32():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ESP32_IP, ESP32_PORT))
        print("Connected to ESP32")
        return client_socket
    except Exception as e:
        print(f"Failed to connect to ESP32: {e}")
        return None


# Send a command to ESP32
def send_command(client_socket, command):
    try:
        client_socket.sendall((command + "\n").encode())
        print(f"Command sent: {command}")
    except Exception as e:
        print(f"Failed to send command: {e}")


# Key press event handler
def on_press(key, client_socket):
    try:
        if hasattr(key, "char") and key.char in COMMANDS:
            send_command(client_socket, COMMANDS[key.char])
    except AttributeError:
        pass


# Key release event handler
def on_release(key, client_socket):
    try:
        if hasattr(key, "char") and key.char in COMMANDS:
            send_command(client_socket, COMMANDS["c"])
    except AttributeError:
        pass


def main():
    client_socket = connect_to_esp32()
    if client_socket is None:
        print("Exiting program")
        return

    # Start listening for keyboard events
    with keyboard.Listener(
        on_press=lambda key: on_press(key, client_socket),
        on_release=lambda key: on_release(key, client_socket),
    ) as listener:
        print("Listening for keyboard inputs... (Press ESC to exit)")
        listener.join()

    # Close the socket connection
    client_socket.close()
    print("Connection closed")


if __name__ == "__main__":
    main()
