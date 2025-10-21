import os
import uuid
import email
import time
import logging
import imaplib
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from email.utils import parsedate_to_datetime

from email_integration.tasks import process_attachment_with_gemini
from email_integration.models import EmailAttachment

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Runs a persistent IMAP IDLE worker to listen for new emails and trigger processing."

    def handle(self, *args, **kwargs):
        host = os.getenv("MAILU_IMAP_HOST")
        user = os.getenv("MAILU_IMAP_USER")
        password = os.getenv("MAILU_IMAP_PASS")

        logger.info("Starting IMAP IDLE worker...")
        self.stdout.write(self.style.SUCCESS(f"Preparing to connect to IMAP server..."))
        self.stdout.write(f"  Host: {host}")
        self.stdout.write(f"  User: {user}")

        # Mask the password for security before logging
        logger.info(f"Connecting to IMAP server: Host={host}, User={user}")
        masked_password = f"{password[:2]}...{password[-2:]}" if password and len(password) > 4 else "(password is short or not set)"
        self.stdout.write(f"  Password: {masked_password}")
        self.stdout.write(f"Connecting...")

        while True: # Main loop to handle reconnects
            try:
                # --- FIX STARTS HERE ---
                # CORRECTED: Set ssl=True to connect securely from the start using port 993.
                server = IMAPClient(host, ssl=True, timeout=300)

                # REMOVED: The server.starttls() line is no longer needed and has been removed.
                # --- FIX ENDS HERE ---

                server.login(user, password)

                server.select_folder('INBOX')
                logger.info(f"Successfully connected and selected INBOX folder.")
                self.stdout.write(self.style.SUCCESS("Connection successful. Listening for new emails via IDLE..."))

                while True: # IDLE loop
                    try:
                        server.idle()
                        # Check for activity or timeout every 29 minutes (a common keepalive duration)
                        responses = server.idle_check(timeout=29 * 60) 
                        server.idle_done()

                        if responses:
                            logger.info(f"New email activity detected.")
                            self.stdout.write(self.style.SUCCESS("New email activity detected. Fetching unseen messages..."))
                            messages = server.search(['UNSEEN'])
                            for uid, message_data in server.fetch(messages, 'RFC822').items():
                                self.process_message(message_data)
                    except (IMAPClientError, OSError, imaplib.error) as idle_error:
                        logger.error(f"Error during IDLE: {idle_error}")
                        break # Exit inner loop to reconnect

                server.close_folder()
                server.logout()
                logger.info("Disconnected from IMAP server.")
            except (IMAPClientError, OSError, imaplib.error) as e:
                self.stderr.write(self.style.ERROR(f"IMAP connection error: {e}. Reconnecting in 30 seconds..."))
                logger.exception("Connection error occurred:")
                time.sleep(30)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("IMAP worker stopped by user."))
                break # Exit the main loop on Ctrl+C

    def process_message(self, message_data):
        msg = email.message_from_bytes(message_data[b'RFC822'])
        sender = msg.get('From', '')  
        subject = msg.get('Subject', '')
        date_str = msg.get('Date', '')
        email_date_obj = parsedate_to_datetime(date_str) if date_str else None

        for part in msg.walk():
            if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                continue
            
            filename = part.get_filename()
            if filename:
                # Generate a unique filename to prevent overwrites
                unique_name = f"mailu_{uuid.uuid4().hex}_{filename}"
                
                file_content = part.get_payload(decode=True)
                
                # Create the EmailAttachment record in the database
                attachment = EmailAttachment.objects.create(
                    file=ContentFile(file_content, name="attachments/"+unique_name),
                    filename=filename, 
                    sender=sender, 
                    subject=subject, 
                    email_date=email_date_obj
                )
                self.stdout.write(self.style.SUCCESS(f"Saved attachment: {filename} (DB id: {attachment.id})"))
                
                # Trigger the background Gemini processing task
                process_attachment_with_gemini.delay(attachment.id)
                self.stdout.write(self.style.WARNING(f"Triggered Gemini processing for attachment id: {attachment.id}"))
