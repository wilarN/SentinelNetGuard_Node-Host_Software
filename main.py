import os
from srv_src import local_logging, useful, sock
from json import dumps
from os import path, remove
from threading import Event
import time

"""
node_instance_65181a699c889
icoimf42cskplw225gjyn9i9nabze3p3jndjbs37ej4sxwhp4ws3u7pm9n6a9otq
port: 2030
"""

debugging = False

if debugging:
    local_logging.LOGGING_MSG(2, "Debugging mode enabled.")
    # Delete log file if it exists
    if path.exists("log.log"):
        remove("log.log")

    # Delete config file if it exists
    if path.exists("config.json"):
        remove("config.json")


def clear():
    """
    Clears the terminal screen.
    """
    os.system('cls' if os.name == 'nt' else 'clear')


def init():
    local_logging.LOGGING_MSG(1, "-+-+-+-+-[ INITIALIZING NEW RUN ]+-+-+-+-+")
    time.sleep(0)
    local_logging.LOGGING_MSG(1, "Initializing...")
    time.sleep(0)
    local_logging.LOGGING_MSG(1, "Server initializing...")
    time.sleep(0)
    local_logging.LOGGING_MSG(1, "Checking if first run...")
    time.sleep(0)
    try:
        # Check if config file exists
        f = open("config.json")
        f.close()
        if useful.get_config_key("server_unid") == "CHANGE_ME" or useful.get_config_key("private_key") == "CHANGE_ME":
            local_logging.LOGGING_MSG(4, "Config file not configured.")
            exit("Please input node unid into the field in the config file(ex. node_instance_6516b6e739dcb).\n"
                 "Then change the private_key that is unique to your client account.\n"
                 "Then rerun the software.")
    except IOError:
        config_file_structure = {
            "#__INFORMATION__#": "ANTELLO NODE CONFIG FILE --> DO NOT MESS WITH VALUES YOU DONT KNOW WHAT THEY DO.",
            "server_unid": "CHANGE_ME",
            "private_key": "CHANGE_ME",
            "host_ip": "0.0.0.0",
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
        f = open("config.json", "w")
        f.write(cfg_json_format)
        f.close()
        local_logging.LOGGING_MSG(1, "First run detected. Creating config file...")
        time.sleep(1)
        local_logging.LOGGING_MSG(5, "Please configurate the server and rerun...")
        time.sleep(1)
        local_logging.LOGGING_MSG(4, "Config file not configured.")
        exit("Please input node unid into the field in the config file(ex. node_instance_6516b6e739dcb).\n"
             "Then change the private_key that is unique to your client account.\n"
             "Then rerun the software.")

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

        # Potential future menu for the future.
        """
        print("-+-+-+-+-[ ANTELLO NODE HOSTER ]+-+-+-+-+\n"
              "1. Start chatroom\n"
              "2. Extend server lifetime\n"
              "3. Delete server\n"
              "4. Exit\n")
        usr_sel = str(input("Selection: ").lower().strip(" "))
        if usr_sel == "1":
            # Start node socket chatroom
            clear()
            local_logging.LOGGING_MSG(1, "Node Started.")
            sock.start_chatroom(stopping_event, srv)
            local_logging.LOGGING_MSG(1, "Node Taken Offline.")
            stopping_event.set()

        elif usr_sel == "2":
            stopping_event.set()

        elif usr_sel == "3":
            stopping_event.set()

        elif usr_sel == "4":
            local_logging.LOGGING_MSG(2, "Stopping main node thread...")
            stopping_event.set()

        else:
            print("Invalid selection. Please try again.")
            time.sleep(1)
            clear()
        """


def main():
    init()
    srv = useful.local_server(unid="test", owner="test", lifetime=0, destruct_time=-1)
    local_logging.LOGGING_MSG(1, "Server created.")
    time.sleep(0)
    # srv.update_local_cfg()
    # LOGGING_MSG(1, "Server config updated.")

    # fetch the node information using unid and validate using private key.

    if not srv.fetch_node_info():
        local_logging.LOGGING_MSG(4, "Node information fetch failed. Continuing locally, node might not work as intended.")

    stop_event = Event()

    """
    # @REMEMBER Do i use threads or not? If so daemon or not? 
    node_thread = Thread(target=main_node_thread)
    # , daemon=True
    node_thread.start()
    """

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
