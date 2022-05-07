import re
import email
import Utils
import base64
import os.path
import traceback

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


class Mailer:
    def __init__(self):    
        creds = None
        self.service = None
        SCOPES = ['https://mail.google.com/']
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        try:
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())

            self.service = build('gmail', 'v1', credentials=creds)
        except:
            err = traceback.format_exc()
            raise Utils.MailerExecutionError(err)

    def get_updated_story_links(self):
        try:
            results = self.service.users().messages().list(userId = 'me', q = 'from:fiftysixw@gmail.com').execute()

            if results['resultSizeEstimate'] == 0:
                raise Utils.MailNotFoundError('No Mail Found')

            story_links = []                
            self.msgs = results['messages']

            for msg in self.msgs:
                msg = self.service.users().messages().get(userId = 'me', id = msg['id'], format = 'full').execute()
                msg_raw = msg['payload']['parts'][0]['body']['data']
                msg_str = base64.urlsafe_b64decode(msg_raw).decode('utf-8')

                story_links.append(re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', msg_str)[0])

                return story_links
        except Utils.MailNotFoundError:
            raise Utils.MailNotFoundError('No Mail Found')
        except:
            err = traceback.format_exc()
            raise Utils.MailerExecutionError(err)

    def move_links_to_trash(self):
        try:
            for msg in self.msgs:
                self.service.users().messages().trash(userId = 'me', id = msg['id']).execute()
        except:
            err = traceback.format_exc()
            raise Utils.MailerExecutionError(err)

    def close(self):
        if self.service != None:
            self.service.close()
