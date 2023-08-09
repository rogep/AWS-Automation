import datetime
import os
from dataclasses import dataclass

from pydantic import BaseModel, validator


@dataclass
class EnvironmentVariableMissing(Exception):
    message: str


class EnvVar(BaseModel):
    weekday_start: datetime.datetime
    weekday_end: datetime.datetime
    weekend_start: datetime.datetime
    weekend_end: datetime.datetime

    @validator(
        ["weekday_start", "weekday_end", "weekend_start", "weekend_end"],
        pre=True,
    )
    def parse_date(cls, value):
        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S").date()


def get_environment_variables() -> EnvVar:
    try:
        weekday_start = os.environ['WEEKDAY_START']
        weekday_end = os.environ['WEEKDAY_END']
        weekend_start = os.environ['WEEKEND_START']
        weekend_end = os.environ['WEEKEND_END']
        env_var = EnvVar(
            weekday_start=weekday_start,
            weekday_end=weekday_end,
            weekend_start=weekend_start,
            weekend_end=weekend_end,
        )
    except KeyError as err:
        raise EnvironmentVariableMissing(
            f"Environment variable is not set!\n Error: {err}"
        )
    return env_var
