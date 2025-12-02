"""
Management command to sync WhatsApp interactive flows with Meta.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from flows.models import WhatsAppFlow, Flow
from flows.whatsapp_flow_service import WhatsAppFlowService
from meta_integration.models import MetaAppConfig
from flows.definitions.tour_inquiry_whatsapp_flow import TOUR_INQUIRY_WHATSAPP_FLOW, TOUR_INQUIRY_WHATSAPP_FLOW_METADATA
from flows.definitions.date_picker_whatsapp_flow import DATE_PICKER_WHATSAPP_FLOW, DATE_PICKER_WHATSAPP_FLOW_METADATA

class Command(BaseCommand):
    help = 'Sync WhatsApp interactive flows with the Meta platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flow',
            type=str,
            choices=['tour_inquiry', 'date_picker', 'all'],
            default='all',
            help='Which flow to sync (default: all)'
        )
        parser.add_argument(
            '--publish',
            action='store_true',
            help='Publish the flows after syncing'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-sync even if flow already exists'
        )

    def handle(self, *args, **options):
        flow_choice = options['flow']
        publish = options['publish']
        force = options['force']

        try:
            meta_config = MetaAppConfig.objects.get_active_config()
        except MetaAppConfig.DoesNotExist:
            raise CommandError('No active Meta App Configuration found. Please configure one in the admin.')
        except MetaAppConfig.MultipleObjectsReturned:
            raise CommandError('Multiple active Meta App Configurations found. Please ensure only one is active.')

        self.stdout.write(self.style.SUCCESS(f'Using Meta config: {meta_config.name}'))
        service = WhatsAppFlowService(meta_config)
        
        flows_to_sync = []
        if flow_choice in ['tour_inquiry', 'all']:
            flows_to_sync.append({
                'json': TOUR_INQUIRY_WHATSAPP_FLOW,
                'metadata': TOUR_INQUIRY_WHATSAPP_FLOW_METADATA
            })
        if flow_choice in ['date_picker', 'all']:
            flows_to_sync.append({
                'json': DATE_PICKER_WHATSAPP_FLOW,
                'metadata': DATE_PICKER_WHATSAPP_FLOW_METADATA
            })

        if not flows_to_sync:
            raise CommandError(f"No flows selected for syncing with choice '{flow_choice}'.")

        for flow_def in flows_to_sync:
            flow_json = flow_def['json']
            metadata = flow_def['metadata']
            flow_name = metadata['name']
            flow_friendly_name = metadata['friendly_name']
            flow_description = metadata['description']

            self.stdout.write(f"\nProcessing flow: {flow_friendly_name}...")

            try:
                with transaction.atomic():
                    # Get the traditional flow to link to (if specified in metadata)
                    flow_definition = None
                    flow_definition_name = metadata.get('flow_definition_name')
                    if flow_definition_name:
                        try:
                            flow_definition = Flow.objects.get(name=flow_definition_name)
                            self.stdout.write(f'  Found traditional flow: {flow_definition.name}')
                        except Flow.DoesNotExist:
                            self.stdout.write(self.style.WARNING(
                                f'  Warning: Traditional flow "{flow_definition_name}" not found. '
                                'WhatsApp Flow will be created without flow_definition link.'
                            ))
                    
                    whatsapp_flow, created = WhatsAppFlow.objects.get_or_create(
                        name=flow_name,
                        defaults={
                            'friendly_name': flow_friendly_name,
                            'description': flow_description,
                            'flow_json': flow_json,
                            'is_active': metadata.get('is_active', True),
                            'meta_app_config': meta_config,
                            'flow_definition': flow_definition,  # Link to traditional flow
                        }
                    )

                    if not created and not force:
                        if whatsapp_flow.sync_status == 'published':
                            self.stdout.write(self.style.WARNING('  Flow already synced and published. Use --force to re-sync.'))
                            continue

                    if not created:
                        whatsapp_flow.flow_json = flow_json
                        whatsapp_flow.friendly_name = flow_friendly_name
                        whatsapp_flow.description = flow_description
                        whatsapp_flow.is_active = metadata.get('is_active', True)
                        whatsapp_flow.flow_definition = flow_definition  # Update flow_definition link
                        whatsapp_flow.save()
                        self.stdout.write('  Flow record updated in database')
                    else:
                        self.stdout.write(self.style.SUCCESS('  Flow record created in database'))

                    self.stdout.write('  Syncing with Meta...')
                    success = service.sync_flow(whatsapp_flow, publish=publish)

                    if success:
                        status_message = 'synced and published' if publish else 'synced as draft'
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Flow {status_message}! Flow ID: {whatsapp_flow.flow_id}'))
                        if not publish:
                            self.stdout.write(self.style.WARNING('  Note: Flow is in draft mode. Run with --publish to make it live.'))
                    else:
                        self.stdout.write(self.style.ERROR(f'  ✗ Sync failed: {whatsapp_flow.sync_error}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error processing flow: {e}'))
                import traceback
                self.stdout.write(traceback.format_exc())

        self.stdout.write('\n' + self.style.SUCCESS('Done!'))
