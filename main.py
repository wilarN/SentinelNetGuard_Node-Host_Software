import os
import socket

from srv_src import local_logging, useful, sock
from json import dumps
from os import path, remove
from threading import Event
import time
import sys

"""
Copyright © William Johnsson 2023 

This code is protected by copyright law. No license is granted. Unauthorized use, modification, or distribution is prohibited.
Contact https://github.com/wilarN for more information.
"""

debugging = False

pre_text = None
part1_text = None
part2_text = None
whitelist_text = None

i = 1
while i < len(sys.argv):
    if sys.argv[i] == '-pre':
        # Check if there's a value after '-pre'
        if i + 1 < len(sys.argv):
            pre_text = sys.argv[i + 1]
            i += 1  # Skip the value
        else:
            print("'-pre' argument is missing its value.")
    elif sys.argv[i] == '-part1':
        if i + 1 < len(sys.argv):
            part1_text = sys.argv[i + 1]
            i += 1
        else:
            print("'-part1' argument is missing its value.")
    elif sys.argv[i] == '-part2':
        if i + 1 < len(sys.argv):
            part2_text = sys.argv[i + 1]
            i += 1
        else:
            print("'-part2' argument is missing its value")
    elif sys.argv[i] == '-whitelist':
        if i + 1 < len(sys.argv):
            whitelist_text = sys.argv[i + 1]
            i += 1
        else:
            print("'-whitelist' argument is missing its value")
    else:
        print(f"Unknown argument: {sys.argv[i]}")

    i += 1

if debugging:
    local_logging.LOGGING_MSG(2, "Debugging mode enabled.")
    # Delete log file if it exists
    if path.exists(local_logging.logging_file_path):
        remove(local_logging.logging_file_path)

    # Delete config file if it exists
    if path.exists(useful.cfg_file_path):
        remove(useful.cfg_file_path)


def clear():
    """
    Clears the terminal screen.
    """
    os.system('cls' if os.name == 'nt' else 'clear')


clear()


def get_ip():
    try:
        r = useful.requests.get("https://am.i.mullvad.net/ip")
        # Remove new line
        r = r.text.replace("\n", "")
        return r
    except Exception as e:
        print(e)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            s.connect(('10.254.254.254', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '0.0.0.0'
        finally:
            s.close()
        return IP


def pre_install_check():
    return [pre_text, part1_text, part2_text]


def init():
    local_logging.LOGGING_MSG(1, "-+-+-+-+-[ INITIALIZING NEW RUN ]+-+-+-+-+")
    time.sleep(0)
    local_logging.LOGGING_MSG(1, "Initializing...")
    time.sleep(0)
    local_logging.LOGGING_MSG(1, "Server initializing...")
    time.sleep(0)
    local_logging.LOGGING_MSG(1, "Checking if first run...")
    time.sleep(0)
    pre_done = pre_install_check()
    pre_gen = None
    try:
        # Check if config file exists
        f = open(useful.cfg_file_path)
        f.close()
        if useful.get_config_key("server_unid") == "CHANGE_ME" or useful.get_config_key("private_key") == "CHANGE_ME":
            local_logging.LOGGING_MSG(4, "Config file not configured.")
            exit("Please input node unid into the field in the config file(ex. node_instance_6516b6e739dcb).\n"
                 "Then change the private_key that is unique to your client account.\n"
                 "Then rerun the software.")
    except IOError:
        if pre_done[0] is None or pre_done[1] is None or pre_done[2] is None or pre_done[0] != "true":
            new_placeholder = "CHANGE_ME"
            new_placeholder2 = "CHANGE_ME"
            pre_gen = False
        else:
            pre_gen = True
            local_logging.LOGGING_MSG(1, "Detected pre-installation!")
            new_placeholder = pre_done[1]
            new_placeholder2 = pre_done[2]
            print(pre_done[1])
            print(pre_done[2])

        try:
            set_ip = get_ip()
            print(set_ip)
        except Exception as e:
            set_ip = "0.0.0.0"
            print(e)

        config_file_structure = {
            "#__INFORMATION__#": "SENTINELNETGUARD NODE CONFIG FILE --> DO NOT MESS WITH VALUES YOU DONT KNOW WHAT THEY DO.",
            "server_unid": f"{new_placeholder}",
            "private_key": f"{new_placeholder2}",
            "host_ip": f"{set_ip}",
            "host_port": "59923",
            "init_join_msg": "Welcome to this SentinelNetGuard node! /help for help.",
            "first_run": "false",
            "time_created": "",
            "connected_users": "",
            "location": "",
            "node_admins": "",
            "server_owner": "null",
            "server_lifetime": "0",
            "server_destruct_time": "-1",
            "allowed_concurrent_connections": "50",
            "server_url": "sentinel.gibb.club",
            "whitelist": "true"
        }

        cfg_json_format = dumps(config_file_structure, indent=4)
        # Create config file
        f = open(useful.cfg_file_path, "w")
        f.write(cfg_json_format)
        f.close()
        local_logging.LOGGING_MSG(1, "First run detected. Creating config file...")
        time.sleep(1)
        if not pre_gen:
            local_logging.LOGGING_MSG(5, "Please configurate the server and rerun...")
            time.sleep(1)
            print("!!!!!!!")
            local_logging.LOGGING_MSG(4, "Config file at: " + useful.cfg_file_path)
            local_logging.LOGGING_MSG(4, "Logging file at: " + local_logging.logging_file_path)
            print("!!!!!!!")
            time.sleep(2)

            local_logging.LOGGING_MSG(4, "Config file not configured.")
            exit("Please input node unid into the field in the config file(ex. node_instance_6516b6e739dcb).\n"
                 "Then change the private_key that is unique to your client account.\n"
                 "Then rerun the software.")
        else:
            local_logging.LOGGING_MSG(1, "Config file set automatically from pre-initialization.")
            time.sleep(1)
            local_logging.LOGGING_MSG(2, "File configured automatically. To start up the node, run the command ´sennet --start´. \n"
                                         "For more info run ´sennet´ or visit the github page.")
            exit(0)

    # End of init
    local_logging.LOGGING_MSG(1, "Server initialized.")
    time.sleep(0)


def main_node_func(stopping_event, srv):
    """
    Think of this thread as the genesis function.
    """
    clear()
    local_logging.LOGGING_MSG(2, "Main node thread started...")
    while not stopping_event.is_set():
        # For now, just boot up and start the node upon running the script.
        clear()
        local_logging.LOGGING_MSG(1, "Node Started.")
        sock.start_chatroom(stopping_event, srv)
        local_logging.LOGGING_MSG(1, "Node Taken Offline.")
        stopping_event.set()


def main():
    init()
    srv = useful.local_server(pre_whitelist=whitelist_text, unid="test", owner="test", lifetime=0, destruct_time=-1)
    local_logging.LOGGING_MSG(1, "Server created.")
    time.sleep(0)
    # srv.update_local_cfg()
    # LOGGING_MSG(1, "Server config updated.")

    # fetch the node information using unid and validate using private key.

    if not srv.fetch_node_info():
        local_logging.LOGGING_MSG(4,
                                  "Node information fetch failed. Continuing locally, node might not work as intended.")

    stop_event = Event()

    # Main loop
    main_node_func(stop_event, srv)

    # Cleanup below
    srv.set_inactive()
    srv.self_delete()
    local_logging.LOGGING_MSG(1, "Server object deleted.")
    time.sleep(0)
    local_logging.LOGGING_MSG(1, "[Node offline]")
    exit(0)


if __name__ == '__main__':
    main()
