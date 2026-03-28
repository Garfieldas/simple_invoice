from decimal import Decimal


def _number_to_words_lt(n):
    """Convert an integer (0 .. 999 999 999 999) to Lithuanian words."""
    if n == 0:
        return 'nulis'

    ones = [
        '', 'vienas', 'du', 'trys', 'keturi', 'penki',
        'šeši', 'septyni', 'aštuoni', 'devyni',
    ]
    teens = [
        'dešimt', 'vienuolika', 'dvylika', 'trylika', 'keturiolika',
        'penkiolika', 'šešiolika', 'septyniolika', 'aštuoniolika',
        'devyniolika',
    ]
    tens = [
        '', 'dešimt', 'dvidešimt', 'trisdešimt', 'keturiasdešimt',
        'penkiasdešimt', 'šešiasdešimt', 'septyniasdešimt',
        'aštuoniasdešimt', 'devyniasdešimt',
    ]

    def _below_thousand(num):
        parts = []
        if num >= 100:
            h = num // 100
            if h == 1:
                parts.append('vienas šimtas')
            else:
                parts.append(f'{ones[h]} šimtai')
            num %= 100
        if num >= 20:
            parts.append(tens[num // 10])
            num %= 10
        if 10 <= num <= 19:
            parts.append(teens[num - 10])
            num = 0
        if num >= 1:
            parts.append(ones[num])
        return ' '.join(parts)

    def _thousand_form(count):
        if count % 10 == 1 and count % 100 != 11:
            return 'tūkstantis'
        if count % 10 == 0 or (10 <= count % 100 <= 19):
            return 'tūkstančių'
        return 'tūkstančiai'

    def _million_form(count):
        if count % 10 == 1 and count % 100 != 11:
            return 'milijonas'
        if count % 10 == 0 or (10 <= count % 100 <= 19):
            return 'milijonų'
        return 'milijonai'

    def _billion_form(count):
        if count % 10 == 1 and count % 100 != 11:
            return 'milijardas'
        if count % 10 == 0 or (10 <= count % 100 <= 19):
            return 'milijardų'
        return 'milijardai'

    parts = []
    if n >= 1_000_000_000:
        b = n // 1_000_000_000
        parts.append(f'{_below_thousand(b)} {_billion_form(b)}')
        n %= 1_000_000_000
    if n >= 1_000_000:
        m = n // 1_000_000
        parts.append(f'{_below_thousand(m)} {_million_form(m)}')
        n %= 1_000_000
    if n >= 1_000:
        t = n // 1_000
        parts.append(f'{_below_thousand(t)} {_thousand_form(t)}')
        n %= 1_000
    if n > 0:
        parts.append(_below_thousand(n))

    return ' '.join(parts)


def amount_to_words_lt(amount):
    """Convert a Decimal amount to Lithuanian words with EUR currency.

    Example: Decimal('1234.56') -> 'vienas tūkstantis du šimtai trisdešimt keturi EUR ir 56 ct'
    """
    amount = Decimal(str(amount)).quantize(Decimal('0.01'))
    integer_part = int(amount)
    cents = int(round((amount - integer_part) * 100))
    words = _number_to_words_lt(integer_part)
    return f'{words} EUR ir {cents:02d} ct'
