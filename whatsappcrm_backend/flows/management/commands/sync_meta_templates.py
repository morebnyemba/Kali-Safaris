import re
import requests
import json
from django.core.management.base import BaseCommand, CommandError
from .load_notification_templates import NOTIFICATION_TEMPLATES
from meta_integration.models import MetaAppConfig
from jinja2 import Environment, meta as jinja_meta


class Command(BaseCommand):
    help = 'Syncs local notification templates with the Meta WhatsApp Business API.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Prints the API payloads that would be sent without actually sending them.",
        )

    def _delete_template(self, template_name, headers, dry_run=False):
        delete_url = f"https://graph.facebook.com/v20.0/{self.active_config.waba_id}/message_templates?name={template_name}"
        self.stdout.write(f"  Attempting to delete existing template '{template_name}'...")
        if not dry_run:
            return requests.delete(delete_url, headers=headers)

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        try:
            active_config = MetaAppConfig.objects.get_active_config()
            if not all([active_config.waba_id, active_config.access_token]):
                raise CommandError("Active MetaAppConfig is missing 'WhatsApp Business Account ID (WABA ID)' or 'Access Token'.")
        except MetaAppConfig.DoesNotExist:
            raise CommandError("No active MetaAppConfig found. Please configure one in the admin panel.")

        self.stdout.write(self.style.SUCCESS("--- Starting WhatsApp Template Sync with Meta ---"))
        if dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN MODE: No requests will be sent to Meta. ---"))
        
        self.active_config = active_config
        create_api_url = f"https://graph.facebook.com/v20.0/{self.active_config.waba_id}/message_templates"
        headers = {
            "Authorization": f"Bearer {self.active_config.access_token}",
            "Content-Type": "application/json",
        }

        for template_def in NOTIFICATION_TEMPLATES:
            template_name = template_def.get('name')
            original_body = template_def.get('body', '')
            self.stdout.write(f"\nProcessing template: '{template_name}'...")

            # --- 1. Convert Jinja2 to Meta format and extract variables ---
            # This regex correctly finds either a complete Jinja2 logic block (e.g., {% if ... %}...{% endif %})
            # or a simple variable placeholder `{{ ... }}`.
            jinja_parts = re.findall(r'(\{%\s*(?:if|for).*?%\}[\s\S]*?\{%\s*end(?:if|for)\s*%\}|\{\{.*?\}\})', original_body)

            meta_body = original_body
            for idx, part in enumerate(jinja_parts):
                meta_body = meta_body.replace(part, f'{{{{{idx + 1}}}}}', 1)

            # --- 2. Construct the API payload ---
            components = [{"type": "BODY", "text": meta_body}]

            # Add example values for variables to aid Meta's review process
            if jinja_parts:
                # Use the variable names themselves as example values
                example_values = []
                for var in jinja_parts:
                    # Clean up the variable for the example
                    cleaned_var = var.replace('{', '').replace('}', '').strip().split('.')[0]
                    example_values.append(f"[{cleaned_var}]")
                components[0]["example"] = {"body_text": [example_values]}

            # Add button components if they are defined
            if 'buttons' in template_def:
                button_payloads = [{"type": "QUICK_REPLY", "text": text} for text in template_def['buttons'][:10]]
                components.append({"type": "BUTTONS", "buttons": button_payloads})

            payload = {
                "name": template_name,
                "language": "en_US",
                "category": "UTILITY", # Changed from "TRANSACTIONAL" to "UTILITY" as per Meta API update
                "components": components,
            }

            if dry_run:
                self.stdout.write(self.style.NOTICE(f"  [Dry Run] Payload for '{template_name}':"))
                self.stdout.write(json.dumps(payload, indent=2))
                continue

            # --- 3. Send the request to Meta's API ---
            try:
                response = requests.post(create_api_url, headers=headers, json=payload)
                response_data = response.json()

                if response.status_code in [200, 201]:
                    self.stdout.write(self.style.SUCCESS(
                        f"  SUCCESS: Template '{template_name}' created successfully. "
                        f"ID: {response_data.get('id')}"
                    ))
                else:
                    error = response_data.get('error', {})
                    error_message = error.get('message')
                    error_code = error.get('code')

                    # Error code 100 with subcode 2334013 means "Template name already exists"
                    if error_code == 100 and 'already exists' in str(error_message):
                        self.stdout.write(self.style.WARNING(f"  INFO: Template '{template_name}' already exists. Attempting to replace it."))
                        
                        # Attempt to delete the existing template
                        delete_response = self._delete_template(template_name, headers, dry_run)
                        if dry_run or (delete_response and delete_response.json().get('success')):
                            self.stdout.write(self.style.SUCCESS(f"  SUCCESS: Deleted existing template '{template_name}'. Re-creating..."))
                            # Retry creating the template
                            retry_response = requests.post(create_api_url, headers=headers, json=payload)
                            if retry_response.status_code in [200, 201]:
                                self.stdout.write(self.style.SUCCESS(f"  SUCCESS: Re-created template '{template_name}' successfully."))
                            else:
                                self.stdout.write(self.style.ERROR(f"  FAILED to re-create template '{template_name}' after deletion. Error: {retry_response.text}"))
                        else:
                            self.stdout.write(self.style.ERROR(f"  FAILED to delete existing template '{template_name}'. It may be in use or have an unchangeable status. Error: {delete_response.text if delete_response else 'N/A'}"))
                    else:
                        self.stdout.write(self.style.ERROR(
                            f"  FAILED to create template '{template_name}'. "
                            f"Status: {response.status_code}, Error: {error_message}"
                        ))
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"  NETWORK ERROR for template '{template_name}': {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  UNEXPECTED ERROR for template '{template_name}': {e}"))

        self.stdout.write(self.style.SUCCESS("\n--- Template Sync Finished ---"))