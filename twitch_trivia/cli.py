import os
import logging
from datetime import datetime, date

from twitch_trivia.models import JeopardyData
from twitch_trivia import bot
from twitch_trivia import logging_util


def main():

    logger = logging.getLogger("twitch_trivia")
    logging_util.setup_base_logger(logger)

    history_logger = logging.getLogger("twitch_trivia.history")
    logging_util.add_rotating_file_handler(
        history_logger,
        format_str="%(asctime)s\t%(message)s",
        filename=os.environ["HISTORY_LOG"],
        max_bytes=5 * 1024 ** 2,
        backup_count=100,
    )
    submission_logger = logging.getLogger("twitch_trivia.submissions")
    logging_util.add_rotating_file_handler(
        submission_logger,
        format_str="%(asctime)s\t%(message)s",
        filename=os.environ["SUBMISSION_LOG"],
        max_bytes=5 * 1024 ** 2,
        backup_count=100,
    )

    jeopardy_data = JeopardyData(
        csv_filename=os.environ["JEOPARDY_CSV"], points_name=os.environ["POINTS_NAME"]
    )
    jeopardy_data.load()
    jeopardy_data.set_min_date(datetime(2010, 1, 1))
    jeopardy_data.set_value_range(low=100, high=2000)

    twitch_bot = bot.Bot(
        jeopardy_data=jeopardy_data,
        stream_id=str(date.today()),
        duration=int(os.environ["JEOPARDY_DURATION"]),
        points_name=os.environ["POINTS_NAME"],
        cooldown=int(os.environ["JEOPARDY_COOLDOWN"]),
        token=os.environ["TWITCH_IRC_TOKEN"],
        nick=os.environ["TWITCH_BOT_USERNAME"],
        prefix="!",
        initial_channels=[os.environ["TWITCH_CHANNEL"]],
    )
    twitch_bot.run()


if __name__ == "__main__":
    main()
