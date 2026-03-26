from datetime import datetime, timedelta


def update_srs(card, rating: str):
    """
    Update flashcard schedule based on review rating.
    rating: again, hard, good, easy
    """

    today = datetime.utcnow()

    if rating == "again":
        card.interval = 1
        card.repetitions = 0

    elif rating == "hard":
        card.interval = max(1, int(card.interval * 1.2))

    elif rating == "good":
        card.interval = max(1, int(card.interval * card.ease_factor))
        card.repetitions += 1

    elif rating == "easy":
        card.interval = max(1, int(card.interval * card.ease_factor * 1.3))
        card.repetitions += 1
        card.ease_factor += 0.05

    else:
        raise ValueError("Invalid rating")

    card.due_date = today + timedelta(days=card.interval)
    card.last_reviewed = today

    return card