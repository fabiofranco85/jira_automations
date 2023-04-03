import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from jira import JIRA


def _process_env_():
    load_dotenv()
    jira_url = os.getenv("JIRA_URL")
    username = os.getenv("JIRA_USERNAME")
    password = os.getenv("JIRA_PASSWORD")
    project_key = os.getenv("PROJECT_KEY")

    if not jira_url or not username or not password or not project_key:
        print("Please check if all required environment variables are set in the .env file.")
        sys.exit(1)

    return {
        'jira_instance': JIRA(jira_url, basic_auth=(username, password)),
        'project_key': project_key
    }


def get_worklog_tickets(month, year):
    env = _process_env_()
    jira_instance, project_key = env['jira_instance'], env['project_key']

    start_date = datetime(year, month, 1).strftime("%Y-%m-%d")
    end_date = datetime(year, month + 1, 1).strftime("%Y-%m-%d") if month < 12 else datetime(year + 1, 1, 1).strftime(
        "%Y-%m-%d")

    jql_query = f"project = {project_key} AND worklogDate >= {start_date} AND worklogDate < {end_date} AND " \
                f"worklogAuthor = currentUser() ORDER BY id"
    issues = jira_instance.search_issues(jql_query, maxResults=False)
    ticket_ids = [issue.key for issue in issues]

    return ",\n".join(ticket_ids)


def main():
    if len(sys.argv) != 3:
        print("Usage: python jira_worklog_report.py <month> <year>")
        sys.exit(1)

    month, year = int(sys.argv[1]), int(sys.argv[2])
    ticket_ids = get_worklog_tickets(month, year)

    print(ticket_ids)


if __name__ == "__main__":
    main()
