LOOPBACK_HEX = "0100007F"
ESTABLISHED = "01"
STATE_COLUMN = 3


def split_address(address: str) -> tuple[str, int]:
    host, _, port = address.partition(":")
    return host, int(port, 16)


def remote_ports(table: str, local_port: int) -> set[int]:
    ports: set[int] = set()
    for line in table.splitlines()[1:]:
        fields = line.split()
        if len(fields) > STATE_COLUMN and is_client_of(fields, local_port):
            ports.add(split_address(fields[2])[1])
    return ports


def is_client_of(fields: list[str], local_port: int) -> bool:
    local_host, port = split_address(fields[1])
    remote_host, _ = split_address(fields[2])
    return (
        fields[STATE_COLUMN] == ESTABLISHED
        and port == local_port
        and local_host == LOOPBACK_HEX
        and remote_host == LOOPBACK_HEX
    )


class StablePorts:
    def __init__(self) -> None:
        self._previous: set[int] = set()

    def update(self, current: set[int]) -> set[int]:
        stable = current & self._previous
        self._previous = current
        return stable
