from pexpect.exceptions import EOF
from time import sleep
import os
import socket
import pexpect

# Folder of THIS file (…/toolkits/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOCKET_PATH = "/tmp/terminal_socket"

def start_terminal(command: str):
    # terminal.py is expected at: ../utils/terminal.py relative to this file
    terminal_script = os.path.join(BASE_DIR, "..", "utils", "terminal.py")
    terminal_script = os.path.abspath(terminal_script)

    # Start terminal socket server if not running
    if not os.path.exists(SOCKET_PATH):
        # Use python3 on Linux; runs in background
        os.system(f"python3 '{terminal_script}' &")
        sleep(2)

    send_to_terminal(f"$ {command}")

def send_to_terminal(data: str):
    try:
        terminal_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        terminal_socket.connect(SOCKET_PATH)
        terminal_socket.sendall(data.encode("utf-8"))
        terminal_socket.close()
    except Exception as e:
        print(f"Error sending data to socket: {e}")

def read_status(process) -> str:
    try:
        process.expect(EOF)
        data = process.before.decode(errors="ignore")
        send_to_terminal(data)
        return data
    except Exception as e:
        print(f"[ERROR] no data was sent to terminal: {e}")
        return "error"

def handle_sudo(process: pexpect.spawn, password: str = ""):
    if not password:
        password = str(os.getenv("PASS", ""))

    # Use current Linux username (no hardcoded "ha1st")
    user = os.getenv("USER", "user")

    # Match the sudo prompt and send password
    process.expect_exact(f"[sudo] password for {user}: ")
    process.sendline(password)

    result = process.expect(["Sorry, try again.", pexpect.EOF, ".*"])
    read_status(process)

    if result == 0:
        process.close()
        return process, "permission denied"
    return process, "access granted"

def execute(command: str):
    """
    execute is a tool that takes in a command and executes it on the linux
    shell then returns the result.
    """
    print(f"[INFO] current command about to execute {command}")
    start_terminal(command)

    # Run using bash so pipes/redirects work reliably
    child = pexpect.spawn("/bin/bash", ["-lc", command])

    if "sudo" in command:
        child, message = handle_sudo(child)
        if "denied" in message:
            return f"process failed : {message}"

    data = read_status(child)
    return f"the output of the command is {data}"

def get_shell_toolkit():
    return [execute]
