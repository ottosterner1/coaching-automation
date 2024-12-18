"""
File Name: coaching-expiry-reminders.py
Author: Otto Sterner
Date Created: 01-July-2024
Last Modified: 21-July-2024
Python Version: 3.9.4

Description:
This script is used to send reminders to coaches when their coaching certification are set to expire
It will also send a notificatication to parents when their child is eligible to complete a DBS check
Finally, it will send a notice that your certification has expired and cannot coach at Wilton.

Usage:
No arguments are required to run this script. To run the script, use the following command:
    $ python script_name.py
"""

## Import the required libraries
import os
import smtplib
import sys
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
from dateutil.relativedelta import relativedelta
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


############################################
# Function Definitions
###########################################
def send_email(to, cc, subject, body):
    """
    This function sends an email to the specified recipient with the specified subject and body
    
    Arguments:
    to: str: The email address of the recipient
    cc: list: A list of email addresses to CC
    subject: str: The subject of the email
    body: str: The body of the email

    Returns:
    None
    """
    from_email = "headcoach@wiltontennisclub.co.uk"
    
    # Read the password from a file
    with open('config/email_password.txt', 'r') as file:
        password = file.read().strip()

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to
    msg['CC'] = ", ".join(cc)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, [to] + cc, text)
        server.quit()
        print(f"Email sent to {to}")
    except Exception as e:
        print(f"Failed to send email to {to}: {e}")
        exit()


def accreditation_status(accreditation_date):
    """
    This function determines the status of an accreditation based on the date provided

    Arguments:
    accreditation_date: pd.Timestamp: The date of the accreditation

    Returns:
    str: The status of the accreditation
    """
    today = pd.Timestamp(datetime.now())
    one_month_ago = today - relativedelta(months=1)

    if pd.isna(accreditation_date):
        return "invalid date"
    elif one_month_ago <= accreditation_date <= today:
        return "expired within the last month"
    elif accreditation_date < one_month_ago:
        return "expired more than a month ago"
    elif accreditation_date - today <= pd.Timedelta(days=90):
        return "expiring"
    else:
        return "valid"

def get_expiring_documents(coach_documents_pd, course_type_to_check):
    """
    This function filters the coach documents based on the course type provided and 
    returns the expiring and expired documents
    
    Arguments:
    coach_documents_pd: pd.DataFrame: The coach documents DataFrame
    course_type_to_check: str: The course type to check

    Returns:
    pd.DataFrame: The expiring documents
    pd.DataFrame: The expired documents
    """
    coach_documents_pd[course_type_to_check] = pd.to_datetime(coach_documents_pd[course_type_to_check], format='%d/%m/%Y', errors='coerce')
    coach_documents_course_type = coach_documents_pd[["name", "qualification", "email address", course_type_to_check]].copy()
    coach_documents_course_type["expiry_flag"] = coach_documents_course_type[course_type_to_check].apply(accreditation_status)
    
    ## Filter the data based on the expiry flag
    expiring_course = coach_documents_course_type[coach_documents_course_type["expiry_flag"] == "expiring"]
    expired_course = coach_documents_course_type[coach_documents_course_type["expiry_flag"] == "expired within the last month"]

    return expiring_course, expired_course

def get_16_within_1_month(coach_documents_pd):
    """
    This function filters the coach documents based on the date of birth and 
    returns the coaches who have turned 16 within the last month
    
    Arguments:
    coach_documents_pd: pd.DataFrame: The coach documents DataFrame

    Returns:
    pd.DataFrame: The coaches who have turned 16 within the last month
    """
    coach_documents_pd['date of birth'] = pd.to_datetime(coach_documents_pd['date of birth'])
    coach_documents_pd['date_turned_16'] = coach_documents_pd['date of birth'] + pd.DateOffset(years=16)
    current_date = datetime.now()
    coach_documents_pd['first_month_16'] = coach_documents_pd['date_turned_16'].apply(
        lambda x: x <= current_date < x + timedelta(days=30)
    )
    return coach_documents_pd[coach_documents_pd['first_month_16'] == True]

def read_clean_excel_sheet(file_path, sheet_name):
    """
    This function reads an excel sheet and cleans the column names
    
    Arguments:
    file_path: str: The path to the excel file
    sheet_name: str: The name of the sheet to read

    Returns:
    pd.DataFrame: The cleaned DataFrame
    """
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        sys.exit(1)

    # Read the coach documents overview sheet
    coach_documents = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=1, header=0)

    # Remove trailing white space and make the columns lower case and remove new line and make double or more spaces single
    coach_documents.columns = coach_documents.columns.str.lower().str.strip().str.replace("\n", " ").str.replace("  ", " ")

    return coach_documents

def tennis_leaders_check_main(tennis_leader_sheet_name, coach_documents_path, to_expiring_email_addresses, mode):
    """
    Process the tennis leader sheets and notify coaches who have turned 16 within the last month.

    Parameters:
    tennis_leader_sheet_name (list): List of sheet names to process.
    coach_documents_path (str): Path to the Excel file containing coach documents.
    """
    for sheet_name in tennis_leader_sheet_name:
        coach_documents_pd = read_clean_excel_sheet(coach_documents_path, sheet_name)

        # Get the coaches who have turned 16 within the last month
        tennis_leaders_to_notify = get_16_within_1_month(coach_documents_pd)

        # Send emails to the filtered coaches
        for index, coach in tennis_leaders_to_notify.iterrows():
            name = coach['name']
            if mode == "self":
                email = "ottosterner1@icloud.com"
            else:
                email = coach['parent email']

            cc_address = to_expiring_email_addresses
            subject = "DBS Registration Reminder"
            body = (
                f"Dear Parent of {name},\n\n"
                f"{name} has recently turned 16 and is now eligible to complete a DBS check to coach at Wilton Tennis Club. "
                f"Please complete this as soon as possible.\n\n"
                f"Please complete the DBS check at the following link: https://www.lta.org.uk/about-us/safeguarding/criminal-record-checks/dbs-application-form/\n\n"
                f"Once you've done this, please send a copy of your certificate to headcoach@wiltontennisclub.co.uk "
                f"and CC in coachingadmin@wiltontennisclub.co.uk.\n\n"
                f"Kind regards,\n"
                f"Marc Beckles, Head Coach"
            )
            send_email(email, cc_address, subject, body)

def expiring_documents_main(coach_documents_path, course_type_to_check, to_expiring_email_addresses, mode):
    """
    Process the coach documents overview sheet and notify coaches with expiring documents.

    Parameters:
    coach_documents_path (str): Path to the Excel file containing coach documents.
    sheet_name (str): Name of the sheet to process.
    course_type_to_check (list): List of course types to check for expiry.
    """
    for sheet_name in main_check_sheet_names:
        # Read the coach documents overview sheet
        coach_documents_pd = read_clean_excel_sheet(coach_documents_path, sheet_name)

        for course_type in course_type_to_check:
            expiring_course_dataframe, _ = get_expiring_documents(coach_documents_pd, course_type)

            for index, row in expiring_course_dataframe.iterrows():
                name = row['name']
                if mode == "self":
                    email = "ottosterner1@icloud.com"
                else:
                    email = row['email address']
                cc_address = to_expiring_email_addresses
                expiry_date = row[course_type].strftime('%d/%m/%Y')

                if 'lta' in course_type.lower():
                    course_name = 'LTA Accreditation'
                elif 'dbs' in course_type.lower():
                    course_name = 'DBS'
                elif 'pediatric' in course_type.lower():
                    course_name = 'Pediatric First Aid'
                elif 'first' in course_type.lower():
                    course_name = 'First Aid'
                elif 'safeguarding' in course_type.lower():
                    course_name = 'Safeguarding'

                subject = f"REMINDER: {course_name} Expiring Soon"
                body = (
                    f"Dear {name},\n\n"
                    f"Your {course_name} is expiring on {expiry_date}. "
                    f"You've got until this date to get a new one, we suggest you renew or book on this course ASAP as your certificate/accreditation "
                    f"needs to be valid by this date to coach at Wilton Tennis Club.\n\n"
                    f"Once you've done this, please send a completed copy to headcoach@wiltontennisclub.co.uk "
                    f"and CC in coachingadmin@wiltontennisclub.co.uk.\n\n"
                    f"Kind regards,\n"
                    f"Marc Beckles, Head Coach"
                )
                send_email(email, cc_address, subject, body)

def expired_documents_main(coach_documents_path, course_type_to_check, to_expired_email_addresses, mode):
    """
    Process the coach documents overview sheet and notify coaches with expired documents.

    Parameters:
    coach_documents_path (str): Path to the Excel file containing coach documents.
    sheet_name (str): Name of the sheet to process.
    course_type_to_check (list): List of course types to check for expiry.
    """
    for sheet_name in main_check_sheet_names:
        
        # Read the coach documents overview sheet
        coach_documents_pd = read_clean_excel_sheet(coach_documents_path, sheet_name)

        for course_type in course_type_to_check:
            _, expired_course_dataframe = get_expiring_documents(coach_documents_pd, course_type)

            for index, row in expired_course_dataframe.iterrows():
                name = row['name']

                if mode == "self":
                    email = "ottosterner1@icloud.com"
                else:
                    email = row['email address']

                cc_address = to_expired_email_addresses
                expiry_date = row[course_type].strftime('%d/%m/%Y')

                if 'lta' in course_type.lower():
                    course_name = 'LTA Accreditation'
                elif 'dbs' in course_type.lower():
                    course_name = 'DBS'
                elif 'pediatric' in course_type.lower():
                    course_name = 'Pediatric First Aid'
                elif 'first' in course_type.lower():
                    course_name = 'First Aid'
                elif 'safeguarding' in course_type.lower():
                    course_name = 'Safeguarding'

                subject = f"NOTICE: {course_name} Expired"
                body = (
                    f"Dear {name},\n\n"
                    f"Your {course_name} expired on {expiry_date}. "
                    f"You can no longer coach at Wilton Tennis Club until it gets renewed.\n\n"
                    f"Please renew your certificate/accreditation and send a copy to headcoach@wiltontennisclub.co.uk "
                    f"and CC in coachingadmin@wiltontennisclub.co.uk.\n\n"
                    f"Kind regards,\n"
                    f"Marc Beckles, Head Coach"
                )
                send_email(email, cc_address, subject, body)

def download_excel_file(drive, file_id, output_file):
    file = drive.CreateFile({'id': file_id})
    file.GetContentFile(output_file, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

def authenticate_drive():
    gauth = GoogleAuth()
    
    # Ensure this path is correct and the file exists
    settings_file = 'config/client_secrets.json'
    credentials_file = 'config/my_credentials.json'
    
    if not os.path.exists(settings_file):
        raise FileNotFoundError(f'Client secrets file not found: {settings_file}')
    
    # Load client configuration from file
    try:
        gauth.LoadClientConfigFile(settings_file)
    except Exception as e:
        raise ValueError(f'Failed to load client config file: {e}')
    
    # Load saved credentials
    try:
        gauth.LoadCredentialsFile(credentials_file)
    except Exception as e:
        raise ValueError(f'Failed to load credentials file: {e}')
    
    # Check if credentials are missing or expired
    if gauth.credentials is None or gauth.credentials.access_token_expired:
        if gauth.credentials is None:
            print("No credentials found. Starting authentication.")
        elif gauth.credentials.access_token_expired:
            print("Credentials expired. Refreshing token.")
        
        try:
            gauth.LocalWebserverAuth()  # This will open a browser window for authentication
            gauth.SaveCredentialsFile(credentials_file)
        except Exception as e:
            raise RuntimeError(f'Failed to authenticate or save credentials: {e}')
    
    return GoogleDrive(gauth)

# Set up the configuration
service_account_file = 'C:/users/Otto/OneDrive/Tennis/Automation/security/able-reef-427712-s2-5c7e22b7b3b5.json'
excel_file_id = "1TovOV8p-yiKFLlYMz8hW26qtLifGopc-"
output_coaching_file = 'data/Coach Documents Overview Sheet.xlsx'
course_type_to_check = ["lta accreditation", "dbs expiry date", "pediatric fa", "first aid", "safeguarding"]
to_expiring_email_addresses = ["headcoach@wiltontennisclub.co.uk"]
to_expired_email_addresses = ["headcoach@wiltontennisclub.co.uk", "info@wiltontennisclub.co.uk", "coachingadmin@wiltontennisclub.co.uk"]
main_check_sheet_names = ["Program","Assistant"]
tennis_leader_sheet_name = ["Tennis Leaders"]

if __name__ == "__main__":

    drive = authenticate_drive()
    download_excel_file(drive, excel_file_id, output_coaching_file)

    # Prompt the user for the mode
    mode = input("Would you like to run the reminders live or for yourself? (live/self): ").strip().lower()

    if mode == "live":
        ## Process the tennis leader reminders
        tennis_leaders_check_main(tennis_leader_sheet_name, output_coaching_file , to_expiring_email_addresses, mode)  

        ## Process the coach documents expiring reminders
        expiring_documents_main(output_coaching_file, course_type_to_check, to_expiring_email_addresses, mode)

        ## Process the coach documents expired reminders
        expired_documents_main(output_coaching_file, course_type_to_check, to_expired_email_addresses, mode)
    elif mode == "self":
        ## Process the tennis leader reminders
        tennis_leaders_check_main(tennis_leader_sheet_name, output_coaching_file , ["ottosterner1@gmail.com"], mode)  

        ## Process the coach documents expiring reminders
        expiring_documents_main(output_coaching_file, course_type_to_check, ["ottosterner1@gmail.com"], mode)

        ## Process the coach documents expired reminders
        expired_documents_main(output_coaching_file, course_type_to_check, ["ottosterner1@gmail.com"], mode)
    else:
        print("Invalid mode selected. Please choose 'live' or 'self'.")







