from datetime import datetime


def LOGGING_MSG(type:int, message: str, echoed: bool = True):
    """
    Custom logging function. Writes to log.log file and prints to console.
    :param type: 1 = info, 2 = warning, 3 = error, 4 = fatal, 5 = attention, 6 = node client messages
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        f = open("log.log")
        f.close()
    except IOError:
        f = open("log.log", "w")
        f.close()

    # Write to log file
    f = open("log.log", "a")

    f.write("[" + str(current_time) + "] ")
    if type == 1:
        if echoed:
            print("[INFO] " + message)
        f.write("[INFO] " + message + "\n")
    elif type == 2:
        if echoed:
            print("[WARNING] " + message)
        f.write("[WARNING] " + message + "\n")
    elif type == 3:
        if echoed:
            print("[ERROR] " + message)
        f.write("[ERROR] " + message + "\n")
    elif type == 4:
        if echoed:
            print("[FATAL] " + message)
        f.write("[FATAL] " + message + "\n")
    elif type == 5:
        if echoed:
            print("[ATTENTION] " + message)
        f.write("[ATTENTION] " + message + "\n")
    elif type == 6:
        if echoed:
            print("[NODE_CLIENT] " + message)
        f.write("[NODE_CLIENT] " + message + "\n")
    else:
        if echoed:
            print("[WARNING] " + message)
        f.write("[WARNING] " + message + "\n")
    f.close()
