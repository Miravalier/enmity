from enum import IntEnum


class Op(IntEnum):
    DISPATCH = 0  # Receive
    HEARTBEAT = 1  # Send/Receive
    IDENTIFY = 2  # Send
    PRESENCE_UPDATE = 3  # Send
    VOICE_STATE_UPDATE = 4  # Send
    RESUME = 6  # Send
    RECONNECT = 7  # Receive
    REQUEST_GUILD_MEMBERS = 8  # Send
    INVALID_SESSION = 9  # Receive
    HELLO = 10  # Receive
    HEARTBEAT_ACK = 11  # Receive
