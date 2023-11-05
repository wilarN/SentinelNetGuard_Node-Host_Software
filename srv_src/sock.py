import json
import os
import signal
import socket
import threading
import time

from .local_logging import LOGGING_MSG, bcolors as bcolo
from .useful import get_config_key

sentinelnetguard_node_ascii_text = \
    """   _____            __  _            ___   __     __  ______                     ___   __          __   
  / ___/___  ____  / /_(_____  ___  / / | / ___  / /_/ ______  ______ __________/ / | / ____  ____/ ___ 
  \\__ \\/ _ \\/ __ \\/ __/ / __ \\/ _ \\/ /  |/ / _ \\/ __/ / __/ / / / __ `/ ___/ __  /  |/ / __ \\/ __  / _ \\
 ___/ /  __/ / / / /_/ / / / /  __/ / /|  /  __/ /_/ /_/ / /_/ / /_/ / /  / /_/ / /|  / /_/ / /_/ /  __/
/____/\\___/_/ /_/\\__/_/_/ /_/\\___/_/_/ |_/\\___/\\__/\\____/\\__,_/\\__,_/_/   \\__,_/_/ |_/\\____/\\__,_/\\___/"""

help_list = """Node Host Commands:
/stop                    - Stops the node
/help                    - Lists all commands
/say       <message>     - Sends a message to all connected clients
/clear                   - Clears the console
/list                    - Lists all connected clients
/kick      <username>    - Kicks a client from the server
/dm <username> <message> - Sends a message to a specific client
/whitelist <username>    - Invites a client to the server
/whitelist list          - Lists all whitelisted clients
/blacklist <username>    - Bans a client from the server
/extend <time>[h]        - Extends the lifetime of the node by the specified time in hours.
/info                    - Shows information about the node"""

stop_server = False

terminal_prefix = "~$: "


def signal_handler():
    global stop_server
    LOGGING_MSG(1, "Stopping server...")
    stop_server = True


signal.signal(signal.SIGINT, signal_handler)

BUFFER_SIZE = 1024


def terminal_prefix_fixer():
    print(f"\n{bcolo.OKCYAN}" + terminal_prefix + f"{bcolo.ENDC}", end="")


def whitelist_client(whitelist, blacklist, client_username: str, srv=None):
    if client_username in whitelist:
        LOGGING_MSG(2, f"Client {client_username} is already whitelisted.")
    elif client_username in blacklist:
        LOGGING_MSG(2, f"Client {client_username} was blacklisted but is now whitelisted.")
        blacklist.remove(client_username)
        srv.add_to_whitelist(client_username)
    else:
        whitelist.append(client_username)
        srv.add_to_whitelist(client_username)
        srv.update_global_host_info()


def blacklist_client(blacklist, whitelist, client_username: str, srv=None):
    if client_username in blacklist:
        LOGGING_MSG(2, f"Client {client_username} is already blacklisted.")
    else:
        blacklist.append(client_username)
    if client_username in whitelist:
        LOGGING_MSG(2, f"Client {client_username} was whitelisted but is now blacklisted.")
        whitelist.remove(client_username)
        srv.remove_from_whitelist(client_username)


def broadcast_connected_clients(connected_clients):
    for client in connected_clients:
        msg = message_data_mod("[SENTINEL NODE]", client[1][{client[2][0]}])
        client[0].sendall(json.dumps(msg).encode())
        LOGGING_MSG(6, f"[SENTINEL NODE]: {client[1]}[{client[2][0]}]")


def client_alive_ping(conn, connected_clients, stop_event):
    """
    Ping all connected clients to check if they are still alive.
    """
    msg = message_data_mod("[SENTINEL NODE]", "rPING")
    while not stop_event.is_set():
        try:
            # If the name of the client is the same as the one in the connected_clients list, kick the old one.
            for client in connected_clients:
                if client[1] == conn:
                    LOGGING_MSG(1, f"Client {client[1]} kicked. Already connected?")
                    client[0].close()
                    break

            conn.sendall(json.dumps(msg).encode())

            connected_users_data = {
                "data": "connected_users",
                "users": []
            }

            if len(connected_clients) == 0:
                connected_users_data["users"].append("No connected users.")
            else:
                for client in connected_clients:
                    connected_users_data["users"].append(client[1])

            # Send the connected users data only if there are connected users
            if len(connected_clients) > 0:
                LOGGING_MSG(1, "Broadcasted all connected users.", echoed=False)
                conn.sendall(json.dumps(connected_users_data).encode())

            time.sleep(5)
        except Exception as e:
            LOGGING_MSG(3, f"{e}", echoed=False)
            LOGGING_MSG(1, "Client connection appears to be dead.")
            terminal_prefix_fixer()
            for client in connected_clients:
                if client[0] == conn:
                    connected_clients.remove(client)
                    LOGGING_MSG(1, f"Client {client[1]}[{client[2][0]}] removed from connected clients.")
                    terminal_prefix_fixer()
            break


def message_data_mod(prefix, message_data, timestamp=None):
    if timestamp is None:
        timestamp = time.strftime("%H:%M:%S", time.localtime())
    data_mod = {
        "conn_username": prefix,
        "data": message_data,
        "timestamp": timestamp
    }
    return data_mod


def command_listener(stop_event, node_socket, connected_clients, whitelist, blacklist, srv):
    while not stop_event.is_set():
        cmd = str(input(f"{terminal_prefix}")).strip(" ")
        if cmd == "":
            continue
        elif cmd.lower() == "/stop":
            node_socket.close()
            LOGGING_MSG(1, "Node socket closed.")
            stop_event.set()
            LOGGING_MSG(1, "Stopping event set.")
            # break
            exit(0)
        elif cmd.lower() == "/help":
            # All commmands with descriptions
            print(f"{bcolo.OKCYAN}" + help_list + f"{bcolo.ENDC}")
        elif cmd.lower().startswith("/clear"):
            # Cleanup Terminal
            os.system('cls' if os.name == 'nt' else 'clear')
        elif cmd.lower().startswith("/info"):
            print(f"{bcolo.OKCYAN}[ Node Info ]:" + f"{bcolo.ENDC}")
            print(f"{bcolo.OKCYAN}- Unique Node ID: {get_config_key('server_unid')}" + f"{bcolo.ENDC}")
            print(
                f"{bcolo.OKGREEN}- Hosted on: {get_config_key('host_ip')}:{get_config_key('host_port')}" + f"{bcolo.ENDC}")
            print(f"{bcolo.OKGREEN}- Hosted by: {get_config_key('server_owner')}" + f"{bcolo.ENDC}")
            print(f"{bcolo.OKGREEN}- Location: {get_config_key('location')}" + f"{bcolo.ENDC}")
            print(f"{bcolo.OKGREEN}- Current time left: {srv.get_lifetime()}" + f"{bcolo.ENDC}")

        elif cmd.lower().startswith("/list"):
            if len(connected_clients) == 0:
                print(f"{bcolo.OKCYAN}No clients connected to active node." + f"{bcolo.ENDC}")
            else:
                print(f"{bcolo.OKGREEN}Connected Clients: " + f"{bcolo.ENDC}", end="")
                i = 0
                for client in connected_clients:
                    if i == 5:
                        print(" |")
                        print("                  ", end="")
                        i = 0
                    print(f"{bcolo.BOLD} | {client[1]}[{client[2][0]}]" + f"{bcolo.ENDC}", end="")
                    i += 1
                print(" |")
        elif cmd.lower().startswith("/say"):
            parts = cmd.split()
            if len(parts) > 1:
                msg = parts[1]
                for i in range(2, len(parts)):
                    msg += f" {parts[i]}"
                for client in connected_clients:
                    message_modded = message_data_mod("[SENTINEL NODE]", msg)
                    client[0].sendall(json.dumps(message_modded).encode())
                    LOGGING_MSG(6, f"[SENTINEL NODE]: {msg}", echoed=False)
            else:
                print(f"{bcolo.OKCYAN}Usage: /say <message>" + f"{bcolo.ENDC}")
        elif cmd.lower().startswith("/dm"):
            parts = cmd.split()
            if len(parts) > 2:
                user_to_dm = parts[1]
                msg = parts[2]
                for i in range(3, len(parts)):
                    msg += f" {parts[i]}"
                for client in connected_clients:
                    if client[1] == user_to_dm:
                        message_modded = message_data_mod("[SENTINEL NODE]", msg)
                        client[0].sendall(json.dumps(message_modded).encode())
                        LOGGING_MSG(6, f"[SENTINEL NODE]: {msg}", echoed=False)
                        break
            else:
                print(f"{bcolo.OKCYAN}Usage: /dm <username> <message>" + f"{bcolo.ENDC}")
        elif cmd.lower().startswith("/extend"):
            # Extend lifetime of node
            """
            usage: /extend <time> ´in hours´
            if no time is specified, default to 1 hour.
            """
            parts = cmd.split()
            if len(parts) > 1:
                time_to_extend = parts[1]
                if time_to_extend == "":
                    time_to_extend = 1
                try:
                    time_to_extend = int(time_to_extend)
                except ValueError:
                    print(f"{bcolo.OKCYAN}Usage: /extend <time>[h]" + f"{bcolo.ENDC}")
                    continue
                if time_to_extend <= 0:
                    print(f"{bcolo.OKCYAN}Usage: /extend <time>[h]" + f"{bcolo.ENDC}")
                    continue
                srv.extend_node_lifetime(time_to_extend=time_to_extend)
                LOGGING_MSG(1, f"Node lifetime extended by {time_to_extend} hours.")
                terminal_prefix_fixer()

        elif cmd.lower().startswith("/kick"):
            parts = cmd.split()
            if len(parts) > 1:
                user_to_kick = parts[1]
                if parts[1] == "":
                    print(f"{bcolo.OKCYAN}Usage: /kick <username>" + f"{bcolo.ENDC}")
                for client in connected_clients:
                    if client[1] == user_to_kick:
                        LOGGING_MSG(1, f"Client {user_to_kick} kicked.")
                        client[0].close()
                        break
        elif cmd.startswith("/whitelist"):
            # Add client to the whitelist
            parts = cmd.split(maxsplit=1)  # Split the command into two parts
            if len(parts) < 2:
                print(f"{bcolo.OKCYAN}Usage: /whitelist <username>" + f"{bcolo.ENDC}")
            else:
                if parts[1] == "list":
                    print(f"{bcolo.OKCYAN}Whitelisted clients: " + f"{bcolo.ENDC}", end="")
                    i = 0
                    for user in whitelist:
                        if i == 5:
                            print(" |")
                            print("                     ", end="")
                            i = 0
                        print(f"{bcolo.OKGREEN} | {user}" + f"{bcolo.ENDC}", end="")
                        i += 1
                    print(" |")
                    continue
                username = parts[1]
                whitelist_client(whitelist, blacklist, username, srv)
                LOGGING_MSG(2, f"Client '{username}' whitelisted.")
        elif cmd.startswith("/blacklist"):
            # Add client to the blacklist @TODO: Implement
            parts = cmd.split()
            if parts[1] == "":
                print(f"{bcolo.OKCYAN}Usage: /blacklist <username>" + f"{bcolo.ENDC}")
            else:
                blacklist_client(blacklist, whitelist, parts[1], srv)
                LOGGING_MSG(2, f"Client {parts[1]} blacklisted.")

            pass
        else:
            LOGGING_MSG(2, f"Invalid command: '{cmd}' write /help to list all commands.")


def receive_messages(conn, addr, connected_clients, stop_event, whitelist, blacklist, whitelist_enabled,
                     public_key_user_dict):
    conn_username = None
    while not stop_event.is_set():
        try:
            LOGGING_MSG(1, f"\nClient connected from {addr}")
            terminal_prefix_fixer()

            # Make sure client isn't already connected with same port and ip
            for client in connected_clients:
                if client[2][0] == addr[0] and client[2][1] == addr[1]:
                    LOGGING_MSG(2, f"Client {addr} is already connected.")
                    conn.sendall("You are already connected.".encode())
                    conn.close()
                    break
            # Get client information upon connecting, @TODO: validate client information with key
            user_information_json = conn.recv(BUFFER_SIZE).decode()
            # Second part of user_informationjson is another json string containing the user's "username"

            # @REMEMBER some random issues here appearing only sometimes during connection, around 1/4
            # of the time when the client connects. Investigate further! :p
            print(user_information_json)
            user_information_json = json.loads(user_information_json)["data"]

            conn_username = json.loads(user_information_json)["username"]

            # Check if the received JSON string is not empty
            if not user_information_json:
                LOGGING_MSG(3, "Client sent an empty initial JSON string.")
                conn.close()
                break

            user_information = json.loads(user_information_json)
            LOGGING_MSG(6, f"Initial message from {addr}: {user_information_json}")
            terminal_prefix_fixer()
            conn_username = user_information["username"]

            if conn_username in blacklist:
                LOGGING_MSG(2, f"Client {conn_username} is blacklisted.")
                conn.sendall("You are blacklisted from this node.".encode())
                conn.close()
                break
            if conn_username not in whitelist:
                if whitelist_enabled:
                    LOGGING_MSG(2, f"Client {conn_username} is not whitelisted.")
                    conn.sendall("You are not whitelisted on this node.".encode())
                    conn.close()
                    break
                else:
                    continue
            if conn_username in connected_clients:
                LOGGING_MSG(2, f"Client {conn_username} is already connected.")
                conn.sendall("You are already connected.".encode())
                conn.close()
                break

            time_since_last_ping = 0

            """
            Client "tuple" format(Had to change from tuple to list because of the need to modify the time_since_last_ping variable):
            (conn, conn_username, addr, time_since_last_ping)
            [0] = conn
            [1] = conn_username
            [2] = addr
            [3] = time_since_last_ping
            """
            client_tuple = [conn, conn_username, addr, time_since_last_ping]
            connected_clients.append(client_tuple)

            # Initial welcome message
            welcome_message = f"{conn_username} {get_config_key('init_join_msg')}"
            msg = message_data_mod("[SENTINEL NODE]", welcome_message)
            conn.sendall(json.dumps(msg).encode())

            # Further communication
            while not stop_event.is_set():
                # BUFFER_SIZE --> buffer size.
                data = conn.recv(BUFFER_SIZE)
                message_gotten = json.loads(data)["data"]
                timestamp_gotten = json.loads(data)["timestamp"]

                if not data:
                    LOGGING_MSG(1, f"Client [{conn_username}]{addr} disconnected.")
                    terminal_prefix_fixer()
                    connected_clients.remove(client_tuple)
                    conn.close()
                    break
                try:
                    # If it's a json string, parse it and get the "data" key
                    received_data = json.loads(data)
                    # Check if it's a dictionary and contains the "public_key" key
                    data2 = json.loads(received_data["data"])
                    public_key = data2['public_key']
                    public_key_list = public_key.split(":")
                    # public_key_list[0] = "e"
                    # public_key_list[1] = "n"
                    LOGGING_MSG(1, f"Client [{conn_username}]{addr} sent a public key. {public_key_list}")
                    terminal_prefix_fixer()
                    formatted = f"{public_key_list[0]}:{public_key_list[1]}"
                    # If the public key is already in the public_key_user_dict, remove it and add the new one.
                    for key in public_key_user_dict:
                        if public_key_user_dict[key] == formatted:
                            public_key_user_dict.pop(key)
                            break
                    public_key_user_dict[conn_username] = formatted

                    updated_key_dict = {
                        "data": "rUPDATE_PUBLIC_KEYS",
                        "keys": public_key_user_dict
                    }

                    # broadcast an updated public_key_user_dict to all connected clients
                    # for client in connected_clients:
                    for client in connected_clients:
                        # if client[0] is not conn:
                        # message_data_mod("[SENTINEL NODE]",updated_key_dict, None)
                        client[0].sendall(json.dumps(updated_key_dict).encode())

                    print(public_key_user_dict)
                    continue
                except ValueError as e:
                    if message_gotten == "rPONG":
                        client_tuple[3] = 0
                        continue
                    elif message_gotten == "rDISCONNECT":
                        LOGGING_MSG(1, f"Client [{conn_username}]{addr} disconnected.")
                        terminal_prefix_fixer()
                        connected_clients.remove(client_tuple)
                        conn.close()
                        break

                for client_connected in connected_clients:
                    if client_connected[0] is not conn:
                        timestamp = time.strftime("%H:%M:%S", time.localtime())

                        # New method
                        """
                        data_mod structure:
                        {
                            "conn_username": conn_username,
                            "data": data,
                            "timestamp": timestamp
                        }
                        """
                        data_mod = {
                            "conn_username": conn_username,
                            "data": message_gotten,
                            "timestamp": timestamp
                        }

                        client_connected[0].sendall(json.dumps(data_mod).encode())
                    msg = message_data_mod("[SENTINEL NODE]", "rMESSAGE_CALLBACK")
                    conn.sendall(json.dumps(msg).encode())

                LOGGING_MSG(6, f"[{conn_username}]({timestamp_gotten}): {message_gotten}")
                terminal_prefix_fixer()
        except ConnectionResetError:
            # Handle the connection forcibly closed error
            if conn_username is None:
                LOGGING_MSG(1, f"Client {addr} forcibly closed the connection.")
            else:
                LOGGING_MSG(1, f"Client [{conn_username}]{addr} forcibly closed the connection.")
            terminal_prefix_fixer()
            conn.close()
            break
        except Exception as e:
            LOGGING_MSG(3, f"{e}")
            pass
        finally:
            # LOGGING_MSG(1, "Closed connection.")
            break


def get_self_del_thread(stop_event, srv):
    """
    Thread that checks if the node should be shutdown because lifetime is over.
    """
    while not stop_event.is_set():
        if srv.get_lifetime() > 0:
            srv.dec_lifetime()
        else:
            if srv.get_lifetime() < 0:
                LOGGING_MSG(2, "[END] Node is burnt, shutting down...")
                result = srv.destruct()
                if result:
                    LOGGING_MSG(2, "Node successfully deleted.")
                    time.sleep(1)
                    LOGGING_MSG(1, "Deleting node...")
                    time.sleep(1)
                    LOGGING_MSG(3, "Goodbye :)")
                    time.sleep(2)
                    srv.delete_files()
                    stop_event.set()
                else:
                    LOGGING_MSG(3, "Unable to delete node.")
                    # Let node exist locally in case of external server error or downtime.
                    srv.extend_node_lifetime(time_to_extend=1)
                    LOGGING_MSG(2, "Node lifetime extended by 1 hour.")
                break

        time.sleep(1)


def start_chatroom(stop_event, srv):
    if srv.set_active():
        LOGGING_MSG(1, "Server set to active.")
    else:
        LOGGING_MSG(2, "Unable to set node as active but proceeding anyway...")

    if srv.update_global_host_info():
        LOGGING_MSG(1, "IP and PORT online.")

    else:
        LOGGING_MSG(2, "Unable to set IP and PORT online but proceeding anyway...")
        LOGGING_MSG(2, "Clients may have connection issues, please review your cfg and try again.")
        LOGGING_MSG(2, "If the issue persists, please contact support or open an issue.")
        time.sleep(3)

    host = str(get_config_key("host_ip"))
    port = int(get_config_key("host_port"))

    srv.whitelist_enabled_in_cfg()

    whitelist_enabled = srv.get_whitelist_enabled()

    connected_clients = []

    whitelist = []
    blacklist = []

    public_key_user_dict = {

    }
    """ public_key_user_dict structure:
    {
    "username": "public_key" 
    }
    """

    if srv.get_whitelist_enabled():
        LOGGING_MSG(1, "Whitelist enabled.")

        try:
            usnrm = get_config_key("server_owner")
            if usnrm not in srv.get_whitelist():
                whitelist_client(whitelist, blacklist, usnrm, srv)
                LOGGING_MSG(2, f"Client '{usnrm}' whitelisted.")
        except Exception as e:
            LOGGING_MSG(3, f"{e}")
            LOGGING_MSG(3,
                        "Unable to add server owner to whitelist. Make sure you've set it manually in the cfg if you didnt use the pre-setup-script.")

    else:
        LOGGING_MSG(2, "Whitelist disabled in cfg... Unsafe option!!")
        time.sleep(2)

    users_in_whitelist = srv.get_whitelist()
    for user in users_in_whitelist:
        whitelist.append(user)

    allowed_connections = int(get_config_key("allowed_concurrent_connections"))
    print(f"{bcolo.OKCYAN}{sentinelnetguard_node_ascii_text}{bcolo.ENDC}")
    time.sleep(1)
    print(f"{bcolo.OKCYAN}" + help_list + f"{bcolo.ENDC}")

    if not allowed_connections > 0:
        LOGGING_MSG(2, "Defaulting to 50 concurrent client connections.")
        time.sleep(0.3)
        allowed_connections = 50
    LOGGING_MSG(1, f"Allowing {allowed_connections} concurrent client connections.")
    time.sleep(0.3)
    LOGGING_MSG(1, f"Host started on {host}:{port}")
    LOGGING_MSG(5, "[ Welcome to the SentinelNetGuard Node Terminal! /help if you need help. ]")
    time.sleep(0.5)
    print(f"{bcolo.OKCYAN}- Unique Node ID: {get_config_key('server_unid')}" + bcolo.ENDC)
    print(f"{bcolo.OKCYAN}- Hosted on: {get_config_key('host_ip')}:{get_config_key('host_port')}" + bcolo.ENDC)
    print(f"{bcolo.OKCYAN}- Hosted by: {get_config_key('server_owner')}" + bcolo.ENDC)
    print(f"{bcolo.OKCYAN}- Location: {get_config_key('location')}" + bcolo.ENDC)
    print(f"{bcolo.OKCYAN}- Current time left: {srv.get_lifetime()}" + bcolo.ENDC)

    self_destruct_thread = threading.Thread(target=get_self_del_thread, args=(stop_event, srv,))
    self_destruct_thread.start()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as node_socket:
            cmd_thread = threading.Thread(target=command_listener,
                                          args=(stop_event, node_socket, connected_clients, whitelist, blacklist, srv,))
            cmd_thread.start()

            node_socket.bind((host, port))
            node_socket.listen(allowed_connections)
            while not stop_event.is_set():
                conn, addr = node_socket.accept()

                # If conn already exists in connected_clients, remove the exising one and add the new one.
                for client in connected_clients:
                    if client[0] == conn:
                        connected_clients.remove(client)
                        LOGGING_MSG(1, f"Client {client[1]}[{client[2][0]}] reconnected.")
                        terminal_prefix_fixer()

                alive_thread = threading.Thread(target=client_alive_ping, args=(conn, connected_clients, stop_event,))
                alive_thread.start()
                msg = message_data_mod("[SENTINEL NODE]", "rPING")
                conn.sendall(json.dumps(msg).encode())

                thread = threading.Thread(target=receive_messages,
                                          args=(conn, addr, connected_clients, stop_event, whitelist, blacklist,
                                                whitelist_enabled, public_key_user_dict,))
                thread.start()

    except Exception as e:
        LOGGING_MSG(3, f"{e}")
        stop_event.set()
