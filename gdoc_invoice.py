import os
import pickle
import sys
from datetime import datetime

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import logger as logger
from jira_worklog_report import get_worklog_tickets

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
load_dotenv()

german_month_names = {
    1: "Januar",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember",
}


def _get_credentials_():
    creds = None
    if os.path.exists('token.pickle'):
        try:
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        except EOFError:
            os.remove('token.pickle')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def _find_and_replace_(service, doc_id, find_text, replace_text):
    requests = [
        {
            'replaceAllText': {
                'containsText': {
                    'text': find_text,
                    'matchCase': True
                },
                'replaceText': replace_text,
            }
        }
    ]
    result = service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    return result


def create_invoice():
    creds = _get_credentials_()

    template_id = os.getenv('GOOGLE_DOCS_TEMPLATE_ID')
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

    try:
        service = build('docs', 'v1', credentials=creds)

        # Duplicate the template
        drive_service = build('drive', 'v3', credentials=creds)
        body = {
            'name': f'{year}-{month:02d}-Franco-Invoice',
            'parents': [folder_id],
        }
        copied_doc = drive_service.files().copy(fileId=template_id, body=body).execute()
        doc_id = copied_doc['id']

        # Get the month name in German
        month_name_german = german_month_names[month]

        # Get the current date
        current_date = datetime.now().strftime("%d.%m.%Y")

        # Replace placeholders in the new document
        _find_and_replace_(service, doc_id, "{{YEAR}}", str(year))
        _find_and_replace_(service, doc_id, "{{MONTH}}", f"{month:02d}")
        _find_and_replace_(service, doc_id, "{{MONTH_NAME_GERMAN}}", month_name_german)
        _find_and_replace_(service, doc_id, "{{CURRENT_DATE}}", current_date)
        _find_and_replace_(service, doc_id, "{{TICKET_NUMBERS}}", ",\n".join(ticket_ids))

        logger.info(f"Invoice created with ID: {doc_id}")
        return doc_id

    except HttpError as error:
        logger.error(f"An error occurred: {error}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        logger.error("Usage: python gdoc_invoice.py <month> <year>")

    month, year = int(sys.argv[1]), int(sys.argv[2])
    ticket_ids = get_worklog_tickets(month, year)
    create_invoice()
