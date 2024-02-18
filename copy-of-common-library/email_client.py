import imaplib
import email

class EmailClient:
    def __init__(self, server, username, password):
        self.server = server
        self.username = username
        self.password = password
        self.connection = None

    def connect(self):
        self.connection = imaplib.IMAP4_SSL(self.server)
        self.connection.login(self.username, self.password)

    def select_mailbox(self, mailbox):
        self.connection.select(mailbox)

    def search_emails(self, search_criteria='ALL'):
        status, mailbox = self.connection.search(None, search_criteria)
        return mailbox[0].split()

    def fetch_email(self, email_id):
        status, body = self.connection.fetch(email_id, '(RFC822)')
        return email.message_from_bytes(body[0][1])

    def delete_email(self, emails):
        if emails:
            for email_id in emails:
                self.connection.store(email_id, '+FLAGS', '\\Deleted')
            self.connection.expunge()


    def logout(self):
        self.connection.close()
        self.connection.logout()
