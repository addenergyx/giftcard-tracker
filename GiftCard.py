from dataclasses import dataclass, field


class CardNumberError(ValueError):
    """Exception raised when the card number is invalid."""
    pass


class PinError(ValueError):
    """Exception raised when the PIN is invalid."""
    pass


@dataclass(slots=True)
class GiftCard:
    card_number: str
    pin: str
    balance: float = field(default=None, repr=False)

    def __post_init__(self):
        if len(self.card_number) != 16 or not self.card_number.isdigit():
            raise CardNumberError("Card number must be 16 digits long.")
        if len(self.pin) != 4 or not self.pin.isdigit():
            raise PinError("PIN must be 4 digits long.")

    def update_balance(self, new_balance) -> None:
        self.balance = new_balance

    # def __repr__(self):
    #     return f"GiftCard(card_number={self.card_number}, pin={self.pin}, balance={self.balance})"

if __name__ == '__main__':
    giftcard = GiftCard('1111111111111111', '2222')
    print(giftcard)

    # giftcard.balance = 1.0
    # print(giftcard.balance)

