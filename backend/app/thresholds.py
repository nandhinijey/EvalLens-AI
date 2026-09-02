from app.config import SCORE_GREEN_THRESHOLD, SCORE_YELLOW_THRESHOLD


def score_color(avg: float) -> str:
    if avg >= SCORE_GREEN_THRESHOLD:
        return "green"
    if avg >= SCORE_YELLOW_THRESHOLD:
        return "yellow"
    return "red"
