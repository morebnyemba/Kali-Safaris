
import os
import time
import socket
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
import email
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from pdfminer.high_level import extract_text as extract_pdf_text
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

load_dotenv()

def extract_text_from_pdf(filename):
    """Try to extract text from a PDF. If digital, use pdfminer; if scanned, use OCR."""
    try:
        text = extract_pdf_text(filename)
        if text and text.strip():
            return text
    except Exception:
        pass
    # If no text or error, try OCR
    try:
        images = convert_from_path(filename)
        ocr_text = ""
        for img in images:
            ocr_text += pytesseract.image_to_string(img)
        return ocr_text
    except Exception as e:
        return f"[PDF OCR failed: {e}]"

def extract_text_from_image(filename):
    try:
        img = Image.open(filename)
        return pytesseract.image_to_string(img)
    except Exception as e:
        return f"[Image OCR failed: {e}]"

class Command(BaseCommand):
    help = "Run a real-time IMAP IDLE worker for Mailu to process attachments as soon as new mail arrives, with PDF and image text extraction."

    def handle(self, *args, **kwargs):
        host = os.getenv("MAILU_IMAP_HOST")
        user = os.getenv("MAILU_IMAP_USER")
        password = os.getenv("MAILU_IMAP_PASS")
        self.stdout.write(self.style.SUCCESS(f"Connecting to {host} as {user}"))
        try:
            with IMAPClient(host, ssl=True) as server: # Enable SSL/TLS
                server.login(user, password)
                server.select_folder('INBOX')
                self.stdout.write(self.style.SUCCESS("Listening for new emails (IDLE)... Press Ctrl+C to stop."))
                try:
                    while True:
                        try:
                            server.idle()
                            responses = server.idle_check(timeout=29)  # Wait up to 29 seconds for new mail
                            server.idle_done()
                            if responses:
                                self.stdout.write(self.style.SUCCESS("New email detected! Processing..."))
                                messages = server.search(['UNSEEN'])
                                for uid, message_data in server.fetch(messages, 'RFC822').items():
                                    msg = email.message_from_bytes(message_data[b'RFC822'])
                                    for part in msg.walk():
                                        if part.get_content_maintype() == 'multipart':
                                            continue
                                        if part.get('Content-Disposition') is None:
                                            continue
                                        filename = part.get_filename()
                                        if filename:
                                            with open(filename, 'wb') as f:
                                                f.write(part.get_payload(decode=True))
                                            self.stdout.write(self.style.SUCCESS(f"Saved attachment: {filename}"))
                                            # Extract text if PDF or image
                                            ext = filename.lower().split('.')[-1]
                                            if ext == 'pdf':
                                                text = extract_text_from_pdf(filename)
                                                self.stdout.write(self.style.SUCCESS(f"Extracted PDF text:\n{text[:1000]}..."))
                                            elif ext in ('jpg', 'jpeg', 'png', 'bmp', 'tiff'):
                                                text = extract_text_from_image(filename)
                                                self.stdout.write(self.style.SUCCESS(f"Extracted image text:\n{text[:1000]}..."))
                        except (IMAPClientError, OSError, socket.error) as e:
                            self.stderr.write(self.style.ERROR(f"IMAP error: {e}. Reconnecting..."))
                            time.sleep(5) # Shorter sleep before retrying
                            break # Exit inner loop to reconnect
                        time.sleep(1)  # Prevent tight loop
                except KeyboardInterrupt:
                    self.stdout.write(self.style.WARNING("Stopped IMAP IDLE worker."))
        except (IMAPClientError, OSError, socket.error) as e:
            self.stderr.write(self.style.ERROR(f"Failed to connect to IMAP: {e}"))
