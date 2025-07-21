import socket
from typing import Iterable


def build_artnet_dmx(universe: int, data: Iterable[int], *, sequence: int = 0, physical: int = 0) -> bytes:
    """Build an Art-Net ArtDMX packet for the given universe."""
    if universe < 0 or universe >= 32768:
        raise ValueError("Universe must be between 0 and 32767")

    values = bytes(data)
    if len(values) > 512:
        raise ValueError("Art-Net DMX payload cannot exceed 512 bytes")

    packet = bytearray()
    packet.extend(b"Art-Net\x00")
    packet.extend(b"\x00\x50")          # OpCode ArtDMX (little endian)
    packet.extend(b"\x00\x0e")          # Protocol version 14
    packet.append(sequence & 0xFF)
    packet.append(physical & 0xFF)
    packet.extend(universe.to_bytes(2, "little"))
    packet.extend(len(values).to_bytes(2, "big"))
    packet.extend(values)
    return bytes(packet)


def send_artnet_packet(ip: str, port: int, packet: bytes) -> int:
    """Send a raw Art-Net packet to the given host."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        return sock.sendto(packet, (ip, port))

