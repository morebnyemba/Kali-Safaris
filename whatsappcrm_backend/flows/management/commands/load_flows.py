# whatsappcrm_backend/flows/management/commands/load_flows.py

import os
import importlib
from django.core.management.base import BaseCommand
from django.db import transaction
from flows.models import Flow, FlowStep, FlowTransition
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Dynamically discovers and syncs flow definitions from the flows/definitions directory.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Flow Synchronization ---"))

        # --- 1. Discover flow definitions dynamically ---
        flow_definitions = []
        definitions_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'definitions')        

        if not os.path.isdir(definitions_path):
            self.stderr.write(self.style.ERROR(f"Definitions directory not found at: {definitions_path}"))
            return

        for filename in os.listdir(definitions_path):
            if filename.endswith('_flow.py') and not filename.startswith('__'):
                module_name = f"flows.definitions.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for attr_name in dir(module):
                        if attr_name.isupper() and isinstance(getattr(module, attr_name), dict):
                            flow_def = getattr(module, attr_name)
                            if 'name' in flow_def and 'steps' in flow_def:
                                flow_definitions.append(flow_def)
                                self.stdout.write(f"  Discovered flow definition: '{flow_def.get('name')}' in {filename}")
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Error importing or processing {module_name}: {e}"))
                    continue

        if not flow_definitions:
            self.stdout.write(self.style.WARNING("No flow definitions found to load. Exiting."))
            return

        # --- 2. Load the discovered flows ---
        self.stdout.write("\nProcessing discovered flows...")
        for flow_def in flow_definitions:
            self.load_flow(flow_def)

        self.stdout.write(self.style.SUCCESS("\n--- ✅ Flow Synchronization Finished Successfully! ---"))

    def load_flow(self, flow_def: dict):
        flow_name = flow_def['name']
        self.stdout.write(f"  Processing flow: '{flow_name}'...")

        # Create or update the Flow object
        flow, created = Flow.objects.update_or_create(
            name=flow_name,
            defaults={
                'friendly_name': flow_def.get('friendly_name', flow_name.replace('_', ' ').title()),
                'description': flow_def.get('description', ''),
                'trigger_keywords': flow_def.get('trigger_keywords', []),
                'is_active': flow_def.get('is_active', False)
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"    Created new flow '{flow_name}'."))
        else:
            self.stdout.write(f"    Updating existing flow '{flow_name}'. Clearing old steps and transitions.")
            flow.steps.all().delete()

        # Create steps
        steps_map = {}
        for step_def in flow_def.get("steps", []):
            step_name = step_def["name"]
            step = FlowStep.objects.create(
                flow=flow,
                name=step_name,
                step_type=step_def["type"],
                is_entry_point=step_def.get("is_entry_point", False),
                config=step_def.get("config", {})
            )
            steps_map[step_name] = step

        # Create transitions
        for step_def in flow_def.get("steps", []):
            current_step = steps_map.get(step_def["name"])
            if not current_step:
                logger.error(f"Step '{step_def['name']}' not found in steps_map. Skipping transitions.")
                continue

            for i, trans_def in enumerate(step_def.get("transitions", [])):
                next_step_name = trans_def.get("to_step")
                next_step = steps_map.get(next_step_name)
                if next_step:
                    FlowTransition.objects.create(
                        current_step=current_step,
                        next_step=next_step,
                        priority=trans_def.get("priority", i),
                        condition_config=trans_def.get("condition_config", {})
                    )
                else:
                    logger.warning(f"Next step '{next_step_name}' not found for transition from '{current_step.name}'. Skipping.")