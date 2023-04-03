from jira import JIRA
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_worklog_tickets(jira_instance, project_key, month, year):
    start_date = datetime(year, month, 1).strftime("%Y-%m-%d")
    end_date = datetime(year, month + 1, 1).strftime("%Y-%m-%d") if month < 12 else datetime(year + 1, 1, 1).strftime("%Y-%m-%d")

    jql_query = f"project = {project_key} AND worklogDate >= {start_date} AND worklogDate < {end_date} AND worklogAuthor = currentUser() ORDER BY id"
    issues = jira_instance.search_issues(jql_query, maxResults=False)
    ticket_ids = [issue.key for issue in issues]

    return ticket_ids

def main():
    if len(sys.argv) != 3:
        print("Usage: python jira_worklog_report.py <month> <year>")
        sys.exit(1)

    month, year = int(sys.argv[1]), int(sys.argv[2])

    jira_url = os.getenv("JIRA_URL")
    username = os.getenv("JIRA_USERNAME")
    password = os.getenv("JIRA_PASSWORD")
    project_key = os.getenv("PROJECT_KEY")

    if not jira_url or not username or not password or not project_key:
        print("Please check if all required environment variables are set in the .env file.")
        sys.exit(1)
 
    jira_instance = JIRA(jira_url, basic_auth=(username, password))
    ticket_ids = get_worklog_tickets(jira_instance, project_key, month, year)

    print(",\n".join(ticket_ids))

if __name__ == "__main__":
    main()

