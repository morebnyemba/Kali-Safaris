# whatsappcrm_backend/flows/management/commands/load_flow_definitions.py

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.db import transaction
from flows.models import Flow, FlowStep, FlowTransition
from flows.definitions.erp_quote_flow import ERP_QUOTE_FLOW
from flows.definitions.payroll_flow import PAYROLL_SOFTWARE_FLOW
from flows.definitions.fiscalisation_flow import FISCALISATION_FLOW
from flows.definitions.company_details_form_flow import COMPANY_DETAILS_FORM_FLOW
from flows.definitions.solar_installation_flow import SOLAR_INSTALLATION_FLOW
from flows.definitions.site_inspection_flow import SITE_INSPECTION_FLOW
from flows.definitions.site_inspection_flow import SITE_INSPECTION_FLOW # type: ignore
from flows.definitions.main_menu_flow import MAIN_MENU_FLOW
from flows.definitions.simple_add_order_flow import SIMPLE_ADD_ORDER_FLOW # type: ignore
# --- FIX: Import the Starlink flow definition ---
from flows.definitions.starlink_installation_flow import STARLINK_INSTALLATION_FLOW
from flows.definitions.solar_cleaning_flow import SOLAR_CLEANING_FLOW
from flows.definitions.admin_update_order_status_flow import ADMIN_UPDATE_ORDER_STATUS_FLOW
# The import for LEAD_GENERATION_FLOW was already here, but the file was missing.
# Now that we've created lead_gen_flow.py, this will work correctly.
from flows.definitions.lead_gen_flow import LEAD_GENERATION_FLOW

class Command(BaseCommand):
    help = 'Loads or updates predefined conversational flows from definition files into the database.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting to load flow definitions...")
        
        # List of flow definitions to load
        flow_definitions = [
            MAIN_MENU_FLOW,
            LEAD_GENERATION_FLOW,
            ERP_QUOTE_FLOW,
            PAYROLL_SOFTWARE_FLOW,
            FISCALISATION_FLOW,
            COMPANY_DETAILS_FORM_FLOW,
            SOLAR_INSTALLATION_FLOW,
            STARLINK_INSTALLATION_FLOW,
            SITE_INSPECTION_FLOW,
            SOLAR_CLEANING_FLOW,
            SIMPLE_ADD_ORDER_FLOW,
            ADMIN_UPDATE_ORDER_STATUS_FLOW,
        ]

        for flow_def in flow_definitions:
            self.load_flow(flow_def)

        self.stdout.write(self.style.SUCCESS("Successfully loaded all flow definitions."))

    def load_flow(self, flow_def: dict):
        flow_name = flow_def['name']
        self.stdout.write(f"  Processing flow: '{flow_name}'...")

        # Pop 'is_active' to handle it at the end, preventing validation errors.
        is_active_from_def = flow_def.get('is_active', False)

        # Create or update the Flow object, but keep it inactive for now to avoid validation issues
        flow, created = Flow.objects.update_or_create(
            name=flow_name,
            defaults={
                'friendly_name': flow_def.get('friendly_name', flow_name.replace('_', ' ').title()),
                'description': flow_def.get('description', ''),
                'trigger_keywords': flow_def.get('trigger_keywords', []),
                'trigger_config': flow_def.get('trigger_config', {}),
                # --- IMPORTANT: Create/update as inactive first to avoid validation issues ---
                'is_active': False
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"    Created new flow '{flow_name}'."))
        else:
            self.stdout.write(f"    Updating existing flow '{flow_name}'. Clearing old steps and transitions.")
            # Clear all existing steps, which will cascade to transitions, ensuring a clean sync.
            flow.steps.all().delete()

        # First pass: Create all steps from the definition
        steps_in_db = {}
        for step_def in flow_def['steps']:
            step_name = step_def['name']
            step = FlowStep.objects.create(
                flow=flow,
                name=step_name,
                step_type=step_def['type'],
                config=step_def.get('config', {}),
                is_entry_point=step_def.get('is_entry_point', False)
            )
            steps_in_db[step_name] = step
            self.stdout.write(f"      - Created step '{step_name}'.")

        # Second pass: Create transitions, now that all steps are guaranteed to exist
        for step_def in flow_def['steps']:
            current_step_name = step_def['name']
            current_step_obj = steps_in_db[current_step_name]

            for i, trans_def in enumerate(step_def.get('transitions', [])):
                next_step_name = trans_def['to_step']
                if next_step_name not in steps_in_db:
                    raise CommandError(f"Next step '{next_step_name}' not found for transition from '{current_step_name}'. Aborting.")

                FlowTransition.objects.create(
                    current_step=current_step_obj,
                    next_step=steps_in_db[next_step_name],
                    condition_config=trans_def.get('condition_config', {}),
                    priority=trans_def.get('priority', i)
                )
            if step_def.get('transitions'):
                 self.stdout.write(f"      - Created transitions for step '{current_step_name}'.")

        # --- Final step: Set the intended 'is_active' status and run full validation ---
        if is_active_from_def:
            flow.is_active = is_active_from_def
            try:
                # This will run the model's clean() method, which checks for an entry point
                # now that all steps have been created.
                flow.full_clean()
                flow.save(update_fields=['is_active'])
                self.stdout.write(self.style.SUCCESS(f"    Successfully set 'is_active' to {is_active_from_def} for flow '{flow_name}'."))
            except ValidationError as e:
                self.stdout.write(self.style.ERROR(f"    Validation failed for flow '{flow_name}' when trying to activate it. Please check its definition."))
                # Raise CommandError to ensure the transaction is rolled back.
                raise CommandError(f"Validation error for flow '{flow_name}': {e}")