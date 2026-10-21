"""Minimal reproduction of the reported scheduler issue.

Run it and inspect the resulting task-instance states:

    airflow dags test repro_mapped_group_skip
"""
from __future__ import annotations

import pendulum

from airflow.decorators import dag, task, task_group
from airflow.utils.trigger_rule import TriggerRule


@dag(schedule=None, start_date=pendulum.datetime(2024, 1, 1), catchup=False)
def repro_mapped_group_skip():
    @task
    def init():
        return ["a", "b", "c"]

    @task_group
    def tg(message):
        @task
        def imsleepy(message):
            return message

        @task(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
        def imawake():
            print("awake")

        imsleepy(message) >> imawake()

    tg.expand(message=init())


repro_mapped_group_skip()
