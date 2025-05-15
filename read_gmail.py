import imaplib
import email
from email.header import decode_header

# Gmail IMAP server details
imap_server = 'imap.gmail.com'
imap_port = 993  # SSL port

# Your Gmail credentials (use App Password if 2FA is enabled)
email_add_g = 'info@argotek.com.ph'
app_password_g  = 'elbj unos lcaa wiud'

#email_add_g = 'rkveroncruz@argotek.com.ph'
#app_password_g  = 'bcjj pkyo zunh vfax'

def read_emails(email_address, password, folder='INBOX', search_criteria='ALL'):
    try:
        # Connect to the IMAP server
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(email_address, password)

        # Select the mailbox (e.g., INBOX, Sent, Drafts)
        mail.select(folder)

        # Search for emails based on criteria (e.g., 'ALL', 'UNSEEN', 'FROM "sender@example.com"')
        status, email_ids = mail.search(None, search_criteria)
        if status == 'OK':
            for email_id in email_ids[0].split():
                # Fetch the email
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status == 'OK':
                    msg = email.message_from_bytes(msg_data[0][1])

                    # Decode the email headers
                    def decode_header_str(header):
                        decoded_parts = decode_header(header)
                        parts = []
                        for part, charset in decoded_parts:
                            if isinstance(part, bytes):
                                try:
                                    parts.append(part.decode(charset or 'utf-8'))
                                except UnicodeDecodeError:
                                    parts.append(part.decode('latin-1')) # Fallback
                            else:
                                parts.append(part)
                        return ''.join(parts)

                    subject = decode_header_str(msg['Subject'])
                    from_addr = decode_header_str(msg['From'])
                    date = msg['Date']

                    print(f"Subject: {subject}")
                    print(f"From: {from_addr}")
                    print(f"Date: {date}")

                    # You can now process the email content
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                try:
                                    body = part.get_payload(decode=True).decode()
                                    print(f"Body:\n{body}\n---")
                                except UnicodeDecodeError:
                                    body = part.get_payload(decode=True).decode('latin-1')
                                    print(f"Body (decoded with latin-1):\n{body}\n---")
                            elif content_type == "text/html" and "attachment" not in content_disposition:
                                html_body = part.get_payload(decode=True).decode()
                                # You might want to parse the HTML
                                # print(f"HTML Body:\n{html_body}\n---")
                            elif "attachment" in content_disposition:
                                filename = part.get_filename()
                                if filename:
                                    decoded_filename = decode_header_str(filename)
                                    print(f"Attachment: {decoded_filename}")
                                    # You can save the attachment here

                    else:
                        content_type = msg.get_content_type()
                        if content_type == "text/plain":
                            try:
                                body = msg.get_payload(decode=True).decode()
                                print(f"Body:\n{body}\n---")
                            except UnicodeDecodeError:
                                body = msg.get_payload(decode=True).decode('latin-1')
                                print(f"Body (decoded with latin-1):\n{body}\n---")
                        elif content_type == "text/html":
                            html_body = msg.get_payload(decode=True).decode()
                            # print(f"HTML Body:\n{html_body}\n---")

        else:
            print(f"Error searching emails: {status}")

        print("Done.")

        # Logout from the IMAP server
        mail.logout()

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    read_emails(email_add_g, app_password_g, folder='INBOX', search_criteria='ALL')
    # You can change the folder and search criteria as needed
    # For example, to read only unread emails in the Inbox:
    # read_emails(email_address, password, folder='INBOX', search_criteria='UNSEEN')
    # To search for emails from a specific sender:
    # read_emails(email_address, password, folder='INBOX', search_criteria='FROM "specific@example.com"')
    # To search for emails with a specific subject:
    # read_emails(email_address, password, folder='INBOX', search_criteria='SUBJECT "Important Update"')