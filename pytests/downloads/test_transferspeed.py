from kondor.downloads.transferspeed import TransferSpeed

TWO_KILOBYTES_PER_SECOND = 2000.0
ONE_KILOBYTE_PER_SECOND = 1000.0


def test_reports_bytes_per_second_after_one_second() -> None:
    speed = TransferSpeed()
    speed.restart(0)
    speed.update(4000, 2000)
    assert speed.bytes_per_second() == TWO_KILOBYTES_PER_SECOND


def test_keeps_speed_within_one_second() -> None:
    speed = TransferSpeed()
    speed.restart(0)
    speed.update(1000, 1000)
    speed.update(9000, 999)
    assert speed.bytes_per_second() == ONE_KILOBYTE_PER_SECOND


def test_stop_resets_speed() -> None:
    speed = TransferSpeed()
    speed.restart(0)
    speed.update(1000, 1000)
    speed.stop()
    assert speed.bytes_per_second() == 0.0
