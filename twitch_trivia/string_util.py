import re

from nltk.stem import SnowballStemmer


RE_NON_ALPHA = re.compile(r"[^a-zA-Z0-9 ]+")
RE_SPACES = re.compile(r" +")
RE_HTML_TAGS = re.compile(r"<.*?>")
IGNORED_TERMS = set(["a", "an", "the", "of"])
STEMMER = SnowballStemmer("english")


def cleanse_question(question: str) -> str:
    """Cleans the Jeopardy question text suitable for Twitch chat

    Args:
        question: Question text from Jeopardy dataset
    """
    return RE_HTML_TAGS.sub("", question).strip()


def cleanse_answer(answer: str) -> str:
    """Cleans the Jeopardy answers and user-submitted answers in a consistent way

    Args:
        answer: Answer text
    """
    answer = answer.replace("&", " and ")
    answer = RE_NON_ALPHA.sub(" ", answer)
    return RE_SPACES.sub(" ", answer).lower().strip()


def cleanse_answer_message(answer: str) -> str:
    answer = " ".join(answer.split(" ")[1:])
    return cleanse_answer(answer)


def check_answer(submitted: str, correct: str) -> bool:
    x = [STEMMER.stem(i) for i in submitted.split() if i not in IGNORED_TERMS]
    y = [STEMMER.stem(i) for i in correct.split() if i not in IGNORED_TERMS]
    return x == y


def split_category_and_value(message: str):
    """Takes a Twitch command for a question requests and separates the category / value

    There are 3 cases we must handle:
    - Message only consist of `!jeopardy` command
    - Message possibly has a category and ends with numeric point value
    - Message contains a category

    Args:
        message: Twitch command message
    """
    parts = message.split()
    if len(parts) == 1:
        category = None
        value = None
    elif parts[-1].isdigit():
        category = " ".join(parts[1:-1]) or None
        value = int(parts[-1])
    else:
        category = " ".join(parts[1:])
        value = None
    return category, value
