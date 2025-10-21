import os
import importlib
from django.core.management.base import BaseCommand
from django.db import transaction
from flows.models import Flow, FlowStep, FlowTransition
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Syncs flow definitions from Python files into the database.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting flow synchronization..."))

        # 1. Clear existing flows to prevent duplicates and stale data
        self.stdout.write("Clearing existing flows, steps, and transitions...")
        FlowTransition.objects.all().delete()
        FlowStep.objects.all().delete()
        Flow.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("...Existing data cleared."))

        # 2. Discover and load flow definitions
        definitions_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'definitions')
        
        if not os.path.isdir(definitions_path):
            self.stderr.write(self.style.ERROR(f"Definitions directory not found at: {definitions_path}"))
            return

        flow_definitions = []
        for filename in os.listdir(definitions_path):
            if filename.endswith('_flow.py'):
                module_name = f"flows.definitions.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for attr_name in dir(module):
                        if attr_name.isupper() and isinstance(getattr(module, attr_name), dict):
                            flow_def = getattr(module, attr_name)
                            if 'name' in flow_def and 'steps' in flow_def:
                                flow_definitions.append(flow_def)
                                self.stdout.write(f"  Found flow definition: '{flow_def.get('name')}' in {filename}")
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Error importing or processing {module_name}: {e}. Aborting flow sync."))
                    # Continue to next file
                    continue
        
        if not flow_definitions:
            self.stdout.write(self.style.WARNING("No flow definitions found. Database is now empty of flows."))
            return

        # 3. Create new flows and steps from definitions
        self.stdout.write("\nCreating new flows and steps...")
        step_map = {} # To map step names to their DB objects for transition creation
        for flow_def in flow_definitions:
            try:
                flow_name = flow_def['name']
                flow_instance = Flow.objects.create(
                    name=flow_name,
                    friendly_name=flow_def.get('friendly_name', ''),
                    description=flow_def.get('description', ''),
                    is_active=flow_def.get('is_active', False),
                    trigger_keywords=flow_def.get('trigger_keywords', [])
                )
                self.stdout.write(f"  Created Flow: {flow_name}")

                for step_def in flow_def['steps']:
                    step_name = step_def['name']
                    step_instance = FlowStep.objects.create(
                        flow=flow_instance,
                        name=step_name,
                        step_type=step_def['type'],
                        config=step_def.get('config', {}),
                        is_entry_point=step_def.get('is_entry_point', False)
                    )
                    # Map "flow_name.step_name" to the step object
                    step_map[f"{flow_name}.{step_name}"] = step_instance
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error creating flow or steps for '{flow_def.get('name', 'Unknown')}': {e}"))
                # The transaction will be rolled back, so we can just stop.
                raise

        # 4. Create transitions
        self.stdout.write("\nCreating transitions...")
        for flow_def in flow_definitions:
            flow_name = flow_def['name']
            for step_def in flow_def['steps']:
                current_step_name = step_def['name']
                current_step_key = f"{flow_name}.{current_step_name}"
                current_step_instance = step_map.get(current_step_key)

                if not current_step_instance:
                    self.stderr.write(self.style.WARNING(f"  Could not find step instance for '{current_step_key}' while creating transitions. Skipping."))
                    continue

                for trans_def in step_def.get('transitions', []):
                    next_step_name = trans_def.get('to_step')
                    if not next_step_name:
                        self.stderr.write(self.style.WARNING(f"  Transition in step '{current_step_name}' is missing 'to_step'. Skipping."))
                        continue
                    
                    next_step_key = f"{flow_name}.{next_step_name}"
                    next_step_instance = step_map.get(next_step_key)

                    if not next_step_instance:
                        self.stderr.write(self.style.ERROR(f"  Transition target step '{next_step_name}' not found for step '{current_step_name}' in flow '{flow_name}'. Skipping."))
                        continue
                    
                    try:
                        FlowTransition.objects.create(
                            current_step=current_step_instance,
                            next_step=next_step_instance,
                            condition_config=trans_def.get('condition_config', {}),
                            priority=trans_def.get('priority', 0)
                        )
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"Error creating transition from '{current_step_name}' to '{next_step_name}': {e}"))
                        raise

        self.stdout.write(self.style.SUCCESS("\nFlow synchronization completed successfully!"))