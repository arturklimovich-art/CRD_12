import pytest
from agents.trader.core.ping import ping

def test_ping_returns_pong():
    assert ping() == "pong"

def test_ping_not_none():
    assert ping() is not None
