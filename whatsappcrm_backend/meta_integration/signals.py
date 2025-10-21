from django.dispatch import Signal

# Signal sent when a message fails to send after all retries.
# Providing args: message_instance
message_send_failed = Signal()
