"""Small helper shared by server.py and setup_https.py."""
import socket


def lan_ip():
    """This PC's address on the home network, or None if it can't be worked out."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None
