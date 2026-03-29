from decimal import Decimal

from num2words import num2words


def amount_to_words_lt(amount: Decimal) -> str:
    """
    Convert a Decimal amount to words in Lithuanian currency format.
    param amount: Decimal amount to convert
    return: str amount in words
    """
    amount = amount.quantize(Decimal("0.01"))

    euros = int(amount)
    cents = int((amount - euros) * 100)

    euros_words = num2words(euros, lang="lt")

    return (
        f"{euros_words.capitalize()} eur ir {str(cents).zfill(2)} ct"
    )
