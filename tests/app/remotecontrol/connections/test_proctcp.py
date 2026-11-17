from kondor.app.remotecontrol.connections.proctcp import StablePorts, remote_ports

HEADER = "  sl  local_address rem_address   st tx_queue rx_queue\n"
PORT = 9222
ESTABLISHED_CLIENT = (
    "   0: 0100007F:2406 0100007F:C350 01 00000000:00000000 00:00000000 00000000 1000 0 1\n"
)
LISTENING = "   1: 0100007F:2406 00000000:0000 0A 00000000:00000000 00:00000000 00000000 1000 0 2\n"
OTHER_PORT = (
    "   2: 0100007F:1F90 0100007F:C351 01 00000000:00000000 00:00000000 00000000 1000 0 3\n"
)
REMOTE_HOST = (
    "   3: 0100007F:2406 0A00000A:C352 01 00000000:00000000 00:00000000 00000000 1000 0 4\n"
)
CLIENT_PORT = 0xC350


def test_finds_the_ports_of_established_loopback_clients() -> None:
    table = HEADER + ESTABLISHED_CLIENT + LISTENING + OTHER_PORT + REMOTE_HOST

    assert remote_ports(table, PORT) == {CLIENT_PORT}


def test_reads_an_empty_table() -> None:
    assert remote_ports("", PORT) == set()


def test_shows_a_port_only_after_two_polls() -> None:
    stable = StablePorts()

    assert stable.update({CLIENT_PORT}) == set()
    assert stable.update({CLIENT_PORT}) == {CLIENT_PORT}


def test_ignores_a_port_seen_in_a_single_poll() -> None:
    stable = StablePorts()

    stable.update({CLIENT_PORT})

    assert stable.update(set()) == set()
    assert stable.update({CLIENT_PORT}) == set()
