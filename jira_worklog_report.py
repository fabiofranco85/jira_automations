import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from jira import JIRA

import logger as logger


def _process_env_():
    load_dotenv()
    jira_url = os.getenv("JIRA_URL")
    username = os.getenv("JIRA_USERNAME")
    password = os.getenv("JIRA_PASSWORD")
    project_key = os.getenv("PROJECT_KEY")

    if not jira_url or not username or not password or not project_key:
        logger.error("Please check if all required environment variables are set in the .env file.")

    return JIRA(jira_url, basic_auth=(username, password)), project_key


def get_worked_tickets(month, year):
    logger.info("Getting worklog tickets for the month of %s %s" % (month, year))

    env = _process_env_()
    jira_instance, project_key = env

    start_date = datetime(year, month, 1).strftime("%Y-%m-%d")
    end_date = datetime(year, month + 1, 1).strftime("%Y-%m-%d") if month < 12 else datetime(year + 1, 1, 1).strftime(
        "%Y-%m-%d")

    jql_query = f"project = {project_key} AND worklogDate >= {start_date} AND worklogDate < {end_date} AND " \
                f"worklogAuthor = currentUser() ORDER BY id"
    issues = jira_instance.search_issues(jql_query, maxResults=False)
    ticket_ids = [issue.key for issue in issues]

    tickets_str = ", ".join(ticket_ids)
    logger.info("Tickets found: %s" % tickets_str)

    return ticket_ids


def main():
    if len(sys.argv) != 3:
        logger.error("Usage: python jira_worklog_report.py <month> <year>")

    month, year = int(sys.argv[1]), int(sys.argv[2])
    ticket_ids = get_worked_tickets(month, year)

    print(ticket_ids)


if __name__ == "__main__":
    main()
