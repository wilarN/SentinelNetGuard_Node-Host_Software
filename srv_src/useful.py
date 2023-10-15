import os
import time
import json
import requests

path = ""
# ex. "public/"

# @REMEMBER fix logging here

whitelist_file_path = "/opt/SentinelNetGuard/whitelist.txt"
cfg_file_path = "/opt/SentinelNetGuard/config.json"

#whitelist_file_path = "whitelist.txt"
#cfg_file_path = "config.json"

class local_server:
    def __init__(self, unid="null", owner="null", lifetime=0, destruct_time=-1):
        # Deusctruction time -1 == infinite alive_t
        self.unid = unid
        self.owner = owner
        self.lifetime = lifetime
        self.destruct_time = destruct_time
        self.time_created = ""
        self.connected_users = ""
        self.location = ""
        self.node_admins = ""
        self.server_url = "localhost"
        self.active = False
        self.whitelist_enabled = True

        # Get whitelist
        self.whitelist = self.get_whitelist()

        if not os.path.exists(whitelist_file_path):
            with open(whitelist_file_path, "w") as f:
                f.write("")

    def get_whitelist_enabled(self):
        return self.whitelist_enabled

    def whitelist_enabled_in_cfg(self):
        if get_config_key("whitelist") == "true":
            self.whitelist_enabled = True
        else:
            self.whitelist_enabled = False

    def get_whitelist(self):
        # if whitelist file doesnt exist, create it
        if not os.path.exists(whitelist_file_path):
            with open(whitelist_file_path, "w") as f:
                f.write("")
        # read whitelist from file
        with open(whitelist_file_path, "r") as f:
            whitelist = f.readlines()
        # remove whitespace characters like `\n` at the end of each line
        whitelist = [x.strip() for x in whitelist]
        return whitelist

    def add_to_whitelist(self, username):
        # add username to whitelist
        with open(whitelist_file_path, "a") as f:
            f.write(username + "\n")

    def remove_from_whitelist(self, username):
        # remove username from whitelist
        with open(whitelist_file_path, "r") as f:
            lines = f.readlines()
        with open(whitelist_file_path, "w") as f:
            for line in lines:
                if line.strip("\n") != username:
                    f.write(line)

    def set_active(self):
        """
        Set server to active in db.
        """
        # Get private key and unid from cfg
        priv_key = get_config_key("private_key")
        callback_type = "mgsengfse789fj39p2qjf8920qjf02q9d2a"
        unid = get_config_key("server_unid")
        url_actual = get_config_key("server_url")

        r = requests.get(
            f"https://{url_actual}/{path}create.php?auth={callback_type}&srv_host_callback=true&unid={unid}&pkey={priv_key}")
        # get echoed response
        response = r.text

        # Return node info
        if response == "true":
            self.active = True
            return True
        else:
            self.active = False
            return False

    def set_inactive(self):
        """
        Set server to active in db.
        """
        # Get private key and unid from cfg
        priv_key = get_config_key("private_key")
        callback_type = "dha278hda280hd7829a9cdn7897892"
        unid = get_config_key("server_unid")
        url_actual = get_config_key("server_url")

        r = requests.get(
            f"https://{url_actual}/{path}create.php?auth={callback_type}&srv_host_callback=true&unid={unid}&pkey={priv_key}")
        # get echoed response
        response = r.text

        # Return node info
        if response == "true":
            self.active = False
            return True
        else:
            self.active = True
            return False

    def update_global_host_info(self):
        """
        Get ip and port from cfg and contact webserver
        """
        specified_ip = get_config_key("host_ip")
        specified_port = get_config_key("host_port")

        url_actual = get_config_key("server_url")
        callback_type = "vdnaa2ood2ha7dh2ahajklhcxjzndghoan"
        unid = get_config_key("server_unid")
        priv_key = get_config_key("private_key")

        whitelist = self.get_whitelist()
        whitelist = ",".join(whitelist)
        print("WHITELIST SENT TO DB: ", whitelist)

        successful = requests.get(
            f"https://{url_actual}/{path}create.php?auth={callback_type}&global_update=true&unid={unid}&priv_key={priv_key}&ip={specified_ip}&port={specified_port}&whitelist={whitelist}")
        # Convert response to json
        # print(successful)
        # print(successful.text)
        # Return node info
        if successful.text == "true":
            return True
        else:
            return False

    def get_node_info(self):
        """
        Get node information from webserver callback.
        """
        # Use requests to get node info from api callback
        # http://localhost/antello/public/create.php?auth=ghwhs907fy3vj7890fmw7vh387r3h8f7h3d&srv_host_callback=true&unid=node_instance_65181a699c889&pkey=icoimf42cskplw225gjyn9i9nabze3p3jndjbs37ej4sxwhp4ws3u7pm9n6a9otq

        # Get private key and unid from cfg
        priv_key = get_config_key("private_key")
        callback_type = "ghwhs907fy3vj7890fmw7vh387r3h8f7h3d"
        unid = get_config_key("server_unid")
        url_actual = get_config_key("server_url")

        r = requests.get(
            f"https://{url_actual}/{path}create.php?auth={callback_type}&srv_host_callback=true&unid={unid}&pkey={priv_key}")
        # Convert response to json
        node_info = r.json()
        del r
        # Return node info
        return node_info

    def fetch_node_info(self):
        try:
            info = self.get_node_info()
            print(f"FETCHED NODE INFORAMTION: {info}")

            # Set self variables to node info
            self.unid = info["unid"]
            self.owner = info["owned_by"]
            self.time_created = info["time_created"]
            self.connected_users = info["connected_users"]
            self.location = info["location"]
            self.node_admins = info["node_admins"]

            # Update local config
            self.update_local_cfg()

            return True

        except Exception as e:
            print(f"ERROR {e}")
            return False

    def validate_destruction(self):
        """
        Validate if destruction time has passed.
        :return:
        true or false
        """
        if self.destruct_time == -1:
            return False
        else:
            if self.destruct_time < time.time():
                return True
            else:
                return False

    def self_delete(self):
        """
        Permentantly delete server and node.
        // Alt --> run cleanup script on node.
        :return:
        """

        # LOGGING_MSG(1, "Server " + self.unid + " is being deleted.")
        # Detele object
        del self

    def update_local_cfg(self):
        try:
            write_to_config_key("server_unid", str(self.unid))
            write_to_config_key("server_owner", str(self.owner))
            write_to_config_key("server_lifetime", str(self.lifetime))
            write_to_config_key("server_destruct_time", str(self.destruct_time))
            write_to_config_key("time_created", str(self.time_created))
            write_to_config_key("connected_users", str(self.connected_users))
            write_to_config_key("location", str(self.location))
            write_to_config_key("node_admins", str(self.node_admins))
        except Exception as e:
            print(e)

    def refresh_connected_users(self):
        pass


def write_to_config_key(key: str, value: str):
    """
    Writes to json config file
    """
    try:
        with open(cfg_file_path, 'r') as json_file:
            json_decoded = json.load(json_file)

        json_decoded[key] = value

        with open(cfg_file_path, 'w') as json_file:
            json.dump(json_decoded, json_file, indent=4)
    except Exception as e:
        print(e)


def get_config_key(specific_key: str):
    """
    Reads from json config file key
    """
    with open(cfg_file_path) as json_file:
        json_decoded = json.load(json_file)

    return json_decoded[f'{specific_key}']
