import os
import sys
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import logger as logger
from gdoc_gdrive_utils import _get_credentials_, _find_and_replace_, _duplicate_gdoc_, _download_pdf_
from jira_worklog_report import get_worked_tickets


def _get_month_name_in_german_():
    """
    Get the month name in German. For example, if the month is 1, the function will return "Januar".
    :return: the month name in German
    """
    # Get the month name in German
    german_month_names = {
        1: "Januar", 2: "Februar", 3: "März", 4: "April", 5: "Mai", 6: "Juni",
        7: "Juli", 8: "August", 9: "September", 10: "Oktober", 11: "November", 12: "Dezember",
    }
    month_name_german = german_month_names[month]
    return month_name_german


def generate_invoice():
    """
    Create an invoice for the specified month and year. The invoice will be created as a Google Doc and saved to a folder
    in Google Drive. The PDF version of the invoice will be downloaded to a local folder on the machine.
    :return: the ID of the new Google Doc
    :raise: HttpError if an error occurs while creating the invoice or downloading the PDF version of the invoice.
    """
    # Checks if the environment variables are set
    if not os.getenv('GOOGLE_DOCS_TEMPLATE_ID'):
        raise ValueError("The environment variable GOOGLE_DOCS_TEMPLATE_ID is not set.")
    if not os.getenv('GOOGLE_DRIVE_FOLDER_ID'):
        raise ValueError("The environment variable GOOGLE_DRIVE_FOLDER_ID is not set.")

    # Checks if the credentials.json file exists in the current directory and raises an error if it does not
    if not os.path.exists('credentials.json'):
        raise ValueError("The credentials.json file does not exist in the current directory. "
                         "Please download the credentials.json file from the Google Cloud Console and save it in the "
                         "current directory.")

    # Get credentials
    creds = _get_credentials_()

    # Get the IDs of the template and the folder
    template_id = os.getenv('GOOGLE_DOCS_TEMPLATE_ID')
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

    try:
        docs_service = build('docs', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)

        doc_id = _duplicate_gdoc_(month, year, drive_service, folder_id, template_id)

        # Replace placeholders in the new document
        _find_and_replace_(docs_service, doc_id, [
            ("{{YEAR}}", str(year)),
            ("{{MONTH}}", f"{month:02d}"),
            ("{{MONTH_NAME_GERMAN}}", _get_month_name_in_german_()),
            ("{{CURRENT_DATE}}", datetime.now().strftime("%d.%m.%Y")),
            ("{{TICKET_NUMBERS}}", ",\n".join(ticket_ids)),
        ])

        logger.info(f"Invoice created with ID: {doc_id}")

        _download_pdf_(month, year, doc_id, drive_service)

        return doc_id

    except HttpError as error:
        logger.error(f"An error occurred: {error}")


def _validate_args_():
    """
    Validate the command line arguments. The script expects the month and year as command line arguments.
    :return: None
    """
    global month, year

    # Check that the user has provided the month and year as command line arguments when running the script.
    # If not, log an error message from the logger implementation.
    if len(sys.argv) != 3:
        logger.error("Usage: python invoice_generator.py <month> <year>")

    # Check that the month and year are valid month and year values.
    # If not, log an error message from the logger implementation.
    try:
        month, year = int(sys.argv[1]), int(sys.argv[2])
        datetime(year, month, 1)
    except ValueError:
        logger.error("Invalid month or year")


if __name__ == '__main__':
    _validate_args_()

    # Get the month and year from the command line arguments
    month, year = int(sys.argv[1]), int(sys.argv[2])

    # Get the IDs of the tickets that were worked on during the specified month and year.
    ticket_ids = get_worked_tickets(month, year)

    # Generate the invoice for the specified month and year.
    generate_invoice()
