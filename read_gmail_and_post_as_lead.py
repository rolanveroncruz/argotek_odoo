import imaplib
import email
from email.header import decode_header
from typing import Any
from post_leads import get_config, get_rpc_info, upload_lead
import os


class Lead:
    def __init__(self, message_id:str, count:int, email_id:bytes, subject:str, from_name:str, from_addr:str, date:str, body:str):
        self.count = count
        self.email_id = email_id
        self.message_id = message_id
        self.subject = subject
        self.from_name = from_name
        self.from_addr = from_addr
        self.date = date
        self.body = body

    def __str__(self):
        return f"Lead: #{self.count}\n message_id:{self.message_id}\n  date:{self.date}\n from {self.from_name} <{self.from_addr}>\n subject:{self.subject}\n"


# Gmail IMAP server details
imap_server = 'imap.gmail.com'
imap_port = 993  # SSL port

# Your Gmail credentials (use App Password if 2FA is enabled)
email_add_g = 'info@argotek.com.ph'
app_password_g  = 'elbj unos lcaa wiud'

#email_add_g = 'rkveroncruz@argotek.com.ph'
#app_password_g  = 'bcjj pkyo zunh vfax'

def read_emails(email_address, password, folder='INBOX', search_criteria='ALL') -> list[Lead]:
    leads = []
    try:
        # Connect to the IMAP server
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        mail.login(email_address, password)
        print("Logged in to IMAP server.")

        # status, mailboxes = mail.list()
        # if status == 'OK':
        #      print("Available mailboxes (labels):")
        #      for mailbox in mailboxes:
        #          print(mailbox.decode())
        # else:
        #      print(f"Error listing mailboxes: {mailboxes}")


        # Select the mailbox (e.g., INBOX, Sent, Drafts)
        mail.select(folder, readonly=True)

        # Search for emails based on criteria (e.g., 'ALL', 'UNSEEN', 'FROM "sender@example.com"')
        status, email_ids = mail.search(None, search_criteria)
        if status == 'OK':
            """
            Iterate through the emails here
            """

            for idx, email_id in enumerate(email_ids[0].split()):
                # Fetch the email
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status == 'OK':
                    msg = email.message_from_bytes(msg_data[0][1])

                    # Decode the email headers
                    #end of decode_header_str() definition

                    subject = decode_header_str(msg['Subject'])
                    from_addr = decode_header_str(msg['From'])
                    message_id_str = decode_header_str(msg['Message-ID'])
                    date = msg['Date']
                    try:
                        body = extract_body(msg)
                    except Exception as e:
                        print(f"Error extracting body: {e}")
                        body = "Error extracting body"

                    from_name = parse_sender(from_addr)['name']
                    from_addr = parse_sender(from_addr)['email']
                    lead=Lead(message_id=message_id_str,count=idx+1, email_id=email_id, subject=subject,
                              from_name=from_name, from_addr=from_addr, date=date, body=body)

                    # You can now process the email content
                    leads.append(lead)

        else:
            print(f"Error searching emails: {status}")

        print("Done.")

        # Logout from the IMAP server
        mail.logout()

    except Exception as e:
        print(f"An error occurred: {e}")

    return leads

def parse_sender(sender:str) -> dict[str, Any]:
    sender_parts = sender.split('<')
    if len(sender_parts) == 2:
        return {'name': sender_parts[0].strip(), 'email': sender_parts[1].strip('>')}
    else:
        return {'name': sender, 'email': ''}


def decode_header_str(header):
    decoded_parts = decode_header(header)
    parts = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                parts.append(part.decode(charset or 'utf-8'))
            except UnicodeDecodeError:
                parts.append(part.decode('latin-1'))  # Fallback
        else:
            parts.append(part)
    return ''.join(parts)


def extract_body(msg) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body = part.get_payload(decode=True).decode()
                except UnicodeDecodeError:
                    body = part.get_payload(decode=True).decode('latin-1')
            elif content_type == "text/html" and "attachment" not in content_disposition:
                html_body = part.get_payload(decode=True).decode()
                # You might want to parse the HTML
                # print(f"HTML Body:\n{html_body}\n---")
            elif "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    decoded_filename = decode_header_str(filename)
                    # You can save the attachment here

    else:
        content_type = msg.get_content_type()
        if content_type == "text/plain":
            try:
                body = msg.get_payload(decode=True).decode()
                # print(f"Body:\n{body}\n---")
            except UnicodeDecodeError:
                body = msg.get_payload(decode=True).decode('latin-1')
                print(f"Body (decoded with latin-1):\n{body}\n---")
        elif content_type == "text/html":
            html_body = msg.get_payload(decode=True).decode()
            # print(f"HTML Body:\n{html_body}\n---")
    return body


if __name__ == "__main__":
    # leads is [Lead]
    leads = read_emails(email_add_g, app_password_g, folder='"APSI Sales Inquiries"', search_criteria='ALL')
    config = get_config()
    uid = get_rpc_info(config)
    if not uid :
        print("uid is False, exiting...")
        exit(1)
    print(f"uid:{uid}")
    for lead in leads:
        print(f"{lead}\n")
    set_file = "data/email_message_ids.txt"
    message_id_set = set()
    if os.path.exists(set_file):
        with open(set_file, "r") as f:
            for line in f :
                message_id_set.add(line.strip())

    for lead in leads:
        message_id = lead.message_id
        lead_data = {
            'name': lead.subject,
            'email_from': lead.from_name + '<' + lead.from_addr + '>',
            'phone': '123-456-7890',
            'contact_name': lead.from_name,
            'description': lead.body,
            # Add other relevant fields
            'user_id': 7, # Noel Picaso
            }
        if message_id not in message_id_set:
            lead_id = upload_lead(config, uid ,lead_data)
            print(f"uploaded lead:{lead}\n")
            message_id_set.add(message_id)
            print(f"adding to set: message_id:{message_id}")

    print("writing set to file...")
    with open(set_file, "w") as f:
     for message_id in message_id_set:
         f.write(f"{message_id}\n")

    print("DONE.")
