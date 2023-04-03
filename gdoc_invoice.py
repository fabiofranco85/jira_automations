import os
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from jira_worklog_report import get_worklog_tickets

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']


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


def create_invoice(template_id, year, month):
    creds = _get_credentials_()
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

        # Replace placeholders in the new document
        _find_and_replace_(service, doc_id, "{{YEAR}}", str(year))
        _find_and_replace_(service, doc_id, "{{MONTH}}", f"{month:02d}")  # Use a two-digit format for the month
        _find_and_replace_(service, doc_id, "{{TICKET_NUMBERS}}", ticket_ids)

        print(f"Invoice created with ID: {doc_id}")
        return doc_id

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


if __name__ == '__main__':
    template_id = '1pF0SNyybAN9NOh-p7ktx-lyQZA3BABzX-cTb9Xm4NgU'
    folder_id = '1xcd3q9O_qTJQUo9Wyajw_RE4TmTxoeGa'
    year = 2023
    month = 3
    ticket_ids = get_worklog_tickets(month, year)

    create_invoice(template_id, year, month)
