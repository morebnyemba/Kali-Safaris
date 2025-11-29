# whatsappcrm_backend/flows/management/commands/load_flows_from_defs.py
import os
import importlib.util
from django.core.management.base import BaseCommand
from django.db import transaction
from whatsappcrm_backend.flows.models import Flow, FlowStep, FlowTransition

class Command(BaseCommand):
    help = 'Loads or updates flow definitions from the flows/definitions directory.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting to load flow definitions...")
        
        definitions_path = 'whatsappcrm_backend/flows/definitions'
        if not os.path.isdir(definitions_path):
            self.stdout.write(self.style.ERROR(f"Directory not found: {definitions_path}"))
            return

        for filename in os.listdir(definitions_path):
            if filename.endswith('_flow.py'):
                file_path = os.path.join(definitions_path, filename)
                module_name = f"whatsappcrm_backend.flows.definitions.{filename[:-3]}"
                
                try:
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    for attr_name in dir(module):
                        if attr_name.endswith('_FLOW'):
                            flow_def = getattr(module, attr_name)
                            if isinstance(flow_def, dict):
                                self.process_flow_definition(flow_def)

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing file {filename}: {e}"))

        self.stdout.write(self.style.SUCCESS("Successfully finished loading flow definitions."))

    def process_flow_definition(self, flow_def: dict):
        flow_name = flow_def.get('name')
        if not flow_name:
            self.stdout.write(self.style.WARNING("  - Skipping definition with no name."))
            return

        flow, created = Flow.objects.update_or_create(
            name=flow_name,
            defaults={
                'friendly_name': flow_def.get('friendly_name', ''),
                'description': flow_def.get('description', ''),
                'trigger_keywords': flow_def.get('trigger_keywords', []),
                'is_active': flow_def.get('is_active', False),
                'trigger_config': flow_def.get('trigger_config', {})
            }
        )
        
        if created:
            self.stdout.write(f"  - Created new flow: '{flow_name}'")
        else:
            self.stdout.write(f"  - Updated existing flow: '{flow_name}'")

        # Create/Update steps and transitions
        steps_defs = flow_def.get('steps', [])
        step_objects = {}
        
        # First pass: create all steps
        for step_def in steps_defs:
            step_name = step_def.get('name')
            if not step_name:
                self.stdout.write(self.style.WARNING(f"    - Skipping step with no name in flow '{flow_name}'."))
                continue

            step, created = FlowStep.objects.update_or_create(
                flow=flow,
                name=step_name,
                defaults={
                    'step_type': step_def.get('type'),
                    'config': step_def.get('config', {}),
                    'is_entry_point': step_def.get('is_entry_point', False)
                }
            )
            step_objects[step_name] = step
            if created:
                self.stdout.write(f"    - Created new step: '{step_name}'")
            else:
                self.stdout.write(f"    - Updated step: '{step_name}'")
        
        # Second pass: create all transitions
        FlowTransition.objects.filter(current_step__flow=flow).delete()
        self.stdout.write(f"    - Cleared old transitions for flow '{flow_name}'.")

        for step_def in steps_defs:
            current_step_name = step_def.get('name')
            current_step = step_objects.get(current_step_name)
            if not current_step:
                continue

            transitions_defs = step_def.get('transitions', [])
            for i, transition_def in enumerate(transitions_defs):
                next_step_name = transition_def.get('to_step')
                next_step = step_objects.get(next_step_name)

                if not next_step:
                    self.stdout.write(self.style.WARNING(f"      - Could not find next_step '{next_step_name}' for transition from '{current_step_name}'. Skipping."))
                    continue
                
                FlowTransition.objects.create(
                    current_step=current_step,
                    next_step=next_step,
                    condition_config=transition_def.get('condition_config', {}),
                    priority=i # Use list order as priority
                )
        self.stdout.write(f"    - Created {len(transitions_defs)} transitions for step '{current_step_name}'.")

