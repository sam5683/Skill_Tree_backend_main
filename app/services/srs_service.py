from datetime import datetime, timedelta


MIN_EASE = 1.3
DEFAULT_EASE = 2.5


def update_srs(card, rating: str):
    """
    Improved SM-2 based SRS

    rating:
    - again → forgot
    - hard → struggled
    - good → correct
    - easy → very easy
    """

    today = datetime.utcnow()

    # ensure base values
    if not card.ease_factor or card.ease_factor < MIN_EASE:
        card.ease_factor = DEFAULT_EASE

    if not card.interval:
        card.interval = 1

    if not card.repetitions:
        card.repetitions = 0

    # ------------------------
    # AGAIN (FAIL)
    # ------------------------
    if rating == "again":
        card.repetitions = 0
        card.interval = 1

        # 🔥 punish ease
        card.ease_factor = max(MIN_EASE, card.ease_factor - 0.2)

    # ------------------------
    # HARD
    # ------------------------
    elif rating == "hard":
        card.repetitions += 1

        # slower growth
        card.interval = max(1, int(card.interval * 1.2))

        # slight penalty
        card.ease_factor = max(MIN_EASE, card.ease_factor - 0.05)

    # ------------------------
    # GOOD
    # ------------------------
    elif rating == "good":
        card.repetitions += 1

        if card.repetitions == 1:
            card.interval = 1
        elif card.repetitions == 2:
            card.interval = 3
        else:
            card.interval = int(card.interval * card.ease_factor)

    # ------------------------
    # EASY
    # ------------------------
    elif rating == "easy":
        card.repetitions += 1

        if card.repetitions == 1:
            card.interval = 2
        elif card.repetitions == 2:
            card.interval = 5
        else:
            card.interval = int(card.interval * card.ease_factor * 1.3)

        # reward ease
        card.ease_factor += 0.1

    else:
        raise ValueError("Invalid rating")

    # clamp ease
    card.ease_factor = max(MIN_EASE, card.ease_factor)

    # set dates
    card.due_date = today + timedelta(days=card.interval)
    card.last_reviewed = today

    return card
