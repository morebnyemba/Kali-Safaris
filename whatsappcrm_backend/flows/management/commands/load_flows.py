# whatsappcrm_backend/flows/management/commands/load_flows.py

from django.core.management.base import BaseCommand
from django.db import transaction
from flows.models import Flow, FlowStep, FlowTransition

# Import all your flow definitions here
from flows.definitions.main_menu_flow import MAIN_MENU_FLOW
from flows.definitions.tour_inquiry_flow import TOUR_INQUIRY_FLOW
from flows.definitions.view_available_tours_flow import VIEW_AVAILABLE_TOURS_FLOW

ALL_FLOWS = [
    # Only load the new, relevant flows for Kali Safaris
    MAIN_MENU_FLOW, # This is now the kali_safaris_main_menu
    TOUR_INQUIRY_FLOW,
    VIEW_AVAILABLE_TOURS_FLOW,
]

class Command(BaseCommand):
    help = 'Loads or updates all conversational flows from their definition files.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting to load conversational flows...")

        for flow_def in ALL_FLOWS:
            flow_name = flow_def['name']
            self.stdout.write(f"  Processing flow: '{flow_name}'...")

            # Delete existing steps and transitions for this flow to ensure a clean slate
            FlowStep.objects.filter(flow__name=flow_name).delete()

            flow, created = Flow.objects.update_or_create(
                name=flow_name,
                defaults={k: v for k, v in flow_def.items() if k != 'steps'}
            )

            steps_map = {}
            for step_def in flow_def['steps']:
                step_name = step_def['name']
                step, _ = FlowStep.objects.update_or_create(
                    flow=flow, name=step_name,
                    defaults={k: v for k, v in step_def.items() if k != 'transitions'}
                )
                steps_map[step_name] = step

            for step_def in flow_def['steps']:
                current_step = steps_map[step_def['name']]
                for trans_def in step_def.get('transitions', []):
                    next_step = steps_map[trans_def['to_step']]
                    FlowTransition.objects.create(current_step=current_step, next_step=next_step, **{k: v for k, v in trans_def.items() if k != 'to_step'})

            self.stdout.write(self.style.SUCCESS(f"    Successfully loaded flow '{flow_name}'."))

        self.stdout.write(self.style.SUCCESS("All flows loaded successfully."))