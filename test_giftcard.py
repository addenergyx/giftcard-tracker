import pytest
from GiftCard import GiftCard, CardNumberError, PinError

def test_gift_card_initialisation():
    """Test initialisation with valid inputs."""
    card = GiftCard(card_number='1234567890123456', pin='1234')
    assert card.card_number == '1234567890123456'
    assert card.pin == '1234'
    assert card.balance is None

def test_invalid_card_number_length():
    """Card number must be exactly 16 digits"""
    with pytest.raises(CardNumberError):
        GiftCard(card_number='123', pin='1234')

def test_invalid_card_number_characters():
    """Card number must be numeric"""
    with pytest.raises(CardNumberError):
        GiftCard(card_number='abcdefghij123456', pin='1234')

def test_invalid_pin_length():
    """PIN must be exactly 4 digits"""
    with pytest.raises(PinError):
        GiftCard(card_number='1234567890123456', pin='1')

def test_invalid_pin_characters():
    """PIN must be numeric"""
    with pytest.raises(PinError):
        GiftCard(card_number='1234567890123456', pin='abcd')

def test_update_balance():
    """Ensure balance is updated correctly"""
    card = GiftCard(card_number='1234567890123456', pin='1234')
    card.update_balance(100.00)
    assert card.balance == 100.00

def test_repr():
    """Test the repr method"""
    card = GiftCard(card_number='1234567890123456', pin='1234', balance=100.00)
    assert repr(card) == "GiftCard(card_number=1234567890123456, pin=1234, balance=100.0)"
