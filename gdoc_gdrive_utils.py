import os
import pickle

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

import logger as logger

load_dotenv()


def _get_credentials_():
    """
    Get the credentials for the Google Docs API. If the token.pickle file exists, it will be used. Otherwise, the user
    will be prompted to authenticate. The credentials will be saved to token.pickle for future use. If the token.pickle
    file is corrupted, it will be deleted and the user will be prompted to authenticate again.
    :return: the credentials for the Google API services
    :raises: EOFError if the token.pickle file is corrupted
    """
    creds = None

    # The file token.pickle stores the user's access and refresh tokens, and is created automatically when the
    # authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        try:
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        except EOFError:
            os.remove('token.pickle')

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        # If the credentials are expired, refresh them automatically using the refresh token.
        # Otherwise, prompt the user to log in. This will create a new token.pickle file.
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # If modifying these scopes, delete the file token.pickle.
            scopes = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']

            # The credentials.json file contains the client ID and client secret for the Google API.
            # This file is not added to the repository. It should be added to the .gitignore file.
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run. This will overwrite the existing token.pickle file.
        # Be sure token.pickle is not added to the repository. It should be added to the .gitignore file.
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


def _find_and_replace_(docs_service, doc_id, replacements):
    """
    Find and replace text in a Google Doc. The text to be replaced is specified in the replacements' dictionary.
    :param docs_service: docs service. This is the service that will be used to find and replace text in the document.
    :param doc_id: gdoc ID. This is the ID of the document where the text will be replaced.
    :param replacements: dictionary. The keys are the text to be replaced. The values are the text that will replace the
    text specified by the key.
    :return: None
    """
    requests = []
    for find_text, replace_text in replacements:
        requests.append({
            'replaceAllText': {
                'containsText': {
                    'text': find_text,
                    'matchCase': True
                },
                'replaceText': replace_text,
            }
        })

    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()


def _duplicate_gdoc_(month, year, drive_service, folder_id, template_id):
    """
    Duplicate the template and return the new document ID. The new document will be saved in the folder specified by
    folder_id.
    :param drive_service: drive service. This is the service that will be used to duplicate the template.
    :param folder_id: folder ID. This is the ID of the folder where the new document will be saved.
    :param template_id: template ID. This is the ID of the template document.
    :return: the new document ID
    """
    # Duplicate the template
    body = {
        'name': f'{year}-{month:02d}-Franco-Invoice',
        'parents': [folder_id],
    }
    copied_doc = drive_service.files().copy(fileId=template_id, body=body).execute()
    doc_id = copied_doc['id']
    return doc_id


def _download_pdf_(month, year, doc_id, drive_service):
    """
    Download the PDF version of the invoice and save it to a local folder on the machine.
    :param doc_id: gdoc ID
    :param drive_service: drive service
    :return: None
    """
    # Export the document as a PDF
    pdf_export = drive_service.files().export(fileId=doc_id, mimeType='application/pdf').execute()

    # Save the PDF to a local folder
    local_folder = "invoices"  # Replace with the path to your desired local folder
    os.makedirs(local_folder, exist_ok=True)
    pdf_filename = f"{year}-{month:02d}-Franco-Invoice.pdf"

    pdf_path = os.path.join(local_folder, pdf_filename)
    with open(pdf_path, "wb") as f:
        f.write(pdf_export)

    logger.info(f"PDF saved to: {pdf_path}")
