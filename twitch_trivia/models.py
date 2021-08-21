from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import pandas as pd

from twitch_trivia import string_util


SHOW_NUM = "Show Number"
AIR_DATE = " Air Date"
ROUND = " Round"
CATEGORY = " Category"
VALUE = " Value"
QUESTION = " Question"
ANSWER = " Answer"


@dataclass
class JeopardyQuestion:
    id: int
    air_date: datetime
    category: str
    value: int
    question: str
    answer: str
    points_name: str

    @property
    def clean_question(self):
        return string_util.cleanse_question(self.question)

    @property
    def clean_answer(self):
        return string_util.cleanse_answer(self.answer)

    @property
    def dollars(self):
        return f"${self.value}"

    @property
    def points(self):
        return f"{self.value} {self.points_name}"


class JeopardyData:

    """Class to access jeopardy question from CSV

    Attributes:
        csv_filename: CSV filename source
        full_df: Raw pandas dataframe with all information
        df: Filtered dataframe with eligible questions to ask
    """

    def __init__(self, csv_filename: str, points_name: str = "points"):
        self.csv_filename = csv_filename
        self.points_name = points_name
        self.full_df = None
        self.df = None

    def load(self):
        df = pd.read_csv(
            self.csv_filename, dtype={SHOW_NUM: "int"}, parse_dates=[AIR_DATE]
        )
        df[VALUE] = (
            df[VALUE]
            .apply(lambda x: x.replace("$", "").replace(",", "").replace("None", "-1"))
            .astype("int")
        )
        self.full_df = df
        self.df = df

    def set_min_date(self, date: datetime):
        df = self.df
        self.df = df[df[AIR_DATE] >= date]

    def set_value_range(self, low, high):
        df = self.df
        df = df[df[VALUE] >= low]
        self.df = df[df[VALUE] <= high]

    def random_question(
        self, category: str = None, value: int = None
    ) -> Optional[JeopardyQuestion]:
        df = self.df
        if category:
            df = df[df[CATEGORY] == category.upper()]
        if value:
            df = df[df[VALUE] == value]
        if not df.empty:
            data = df.sample().to_dict()
            row_id, category = list(data[CATEGORY].items())[0]
            air_date = list(data[AIR_DATE].values())[0]
            value = list(data[VALUE].values())[0]
            question = list(data[QUESTION].values())[0]
            answer = list(data[ANSWER].values())[0]
            return JeopardyQuestion(
                id=row_id,
                air_date=air_date,
                category=category,
                value=value,
                question=question,
                answer=answer,
                points_name=self.points_name,
            )

    def random_categories(self, num: int = 1) -> List[str]:
        return self.df[CATEGORY].sample(num).unique().tolist()
