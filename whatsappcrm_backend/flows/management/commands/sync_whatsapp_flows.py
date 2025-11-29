# whatsappcrm_backend/flows/management/commands/sync_whatsapp_flows.py

"""
Management command to sync WhatsApp interactive flows with Meta.
Creates or updates WhatsAppFlow instances and syncs them with Meta's platform.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from flows.models import WhatsAppFlow
from flows.whatsapp_flow_service import WhatsAppFlowService
from meta_integration.models import MetaAppConfig
from flows.definitions.starlink_installation_whatsapp_flow import (
    STARLINK_INSTALLATION_WHATSAPP_FLOW,
    STARLINK_INSTALLATION_FLOW_METADATA
)
from flows.definitions.solar_cleaning_whatsapp_flow import (
    SOLAR_CLEANING_WHATSAPP_FLOW,
    SOLAR_CLEANING_FLOW_METADATA
)
from flows.definitions.solar_installation_whatsapp_flow import (
    SOLAR_INSTALLATION_WHATSAPP_FLOW,
    SOLAR_INSTALLATION_FLOW_METADATA
)
from flows.definitions.site_inspection_whatsapp_flow import (
    SITE_INSPECTION_WHATSAPP_FLOW,
    SITE_INSPECTION_FLOW_METADATA
)
from flows.definitions.loan_application_whatsapp_flow import (
    LOAN_APPLICATION_WHATSAPP_FLOW,
    LOAN_APPLICATION_FLOW_METADATA
)
from flows.definitions.hybrid_installation_whatsapp_flow import (
    HYBRID_INSTALLATION_WHATSAPP_FLOW,
    HYBRID_INSTALLATION_FLOW_METADATA
)
from flows.definitions.custom_furniture_installation_whatsapp_flow import (
    CUSTOM_FURNITURE_INSTALLATION_WHATSAPP_FLOW,
    CUSTOM_FURNITURE_INSTALLATION_FLOW_METADATA
)


class Command(BaseCommand):
    help = 'Sync WhatsApp interactive flows with Meta platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flow',
            type=str,
            choices=['starlink', 'solar_cleaning', 'solar_installation', 'site_inspection', 'loan_application', 'hybrid', 'custom_furniture', 'all'],
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

        # Get active Meta app config
        try:
            meta_config = MetaAppConfig.objects.get_active_config()
        except MetaAppConfig.DoesNotExist:
            raise CommandError('No active Meta App Configuration found. Please configure one in the admin.')
        except MetaAppConfig.MultipleObjectsReturned:
            raise CommandError('Multiple active Meta App Configurations found. Please ensure only one is active.')

        self.stdout.write(self.style.SUCCESS(f'Using Meta config: {meta_config.name}'))

        # Initialize service
        service = WhatsAppFlowService(meta_config)

        # Define flows to sync
        flows_to_sync = []
        
        if flow_choice in ['starlink', 'all']:
            flows_to_sync.append({
                'json': STARLINK_INSTALLATION_WHATSAPP_FLOW,
                'metadata': STARLINK_INSTALLATION_FLOW_METADATA
            })
        
        if flow_choice in ['solar_cleaning', 'all']:
            flows_to_sync.append({
                'json': SOLAR_CLEANING_WHATSAPP_FLOW,
                'metadata': SOLAR_CLEANING_FLOW_METADATA
            })
        
        if flow_choice in ['solar_installation', 'all']:
            flows_to_sync.append({
                'json': SOLAR_INSTALLATION_WHATSAPP_FLOW,
                'metadata': SOLAR_INSTALLATION_FLOW_METADATA
            })
        
        if flow_choice in ['site_inspection', 'all']:
            flows_to_sync.append({
                'json': SITE_INSPECTION_WHATSAPP_FLOW,
                'metadata': SITE_INSPECTION_FLOW_METADATA
            })
        
        if flow_choice in ['loan_application', 'all']:
            flows_to_sync.append({
                'json': LOAN_APPLICATION_WHATSAPP_FLOW,
                'metadata': LOAN_APPLICATION_FLOW_METADATA
            })
        
        if flow_choice in ['hybrid', 'all']:
            flows_to_sync.append({
                'json': HYBRID_INSTALLATION_WHATSAPP_FLOW,
                'metadata': HYBRID_INSTALLATION_FLOW_METADATA
            })
        
        if flow_choice in ['custom_furniture', 'all']:
            flows_to_sync.append({
                'json': CUSTOM_FURNITURE_INSTALLATION_WHATSAPP_FLOW,
                'metadata': CUSTOM_FURNITURE_INSTALLATION_FLOW_METADATA
            })

        # Sync each flow
        for flow_def in flows_to_sync:
            flow_json = flow_def['json']
            metadata = flow_def['metadata']
            
            self.stdout.write(f"\nProcessing flow: {metadata['friendly_name']}...")
            
            try:
                with transaction.atomic():
                    # Get or create WhatsAppFlow instance
                    whatsapp_flow, created = WhatsAppFlow.objects.get_or_create(
                        name=metadata['name'],
                        defaults={
                            'friendly_name': metadata['friendly_name'],
                            'description': metadata['description'],
                            'flow_json': flow_json,
                            'is_active': metadata.get('is_active', False),
                            'meta_app_config': meta_config,
                        }
                    )
                    
                    if not created and not force:
                        if whatsapp_flow.sync_status == 'published':
                            self.stdout.write(
                                self.style.WARNING(
                                    '  Flow already synced and published. Use --force to re-sync.'
                                )
                            )
                            continue
                    
                    if not created:
                        # Update existing flow
                        whatsapp_flow.flow_json = flow_json
                        whatsapp_flow.friendly_name = metadata['friendly_name']
                        whatsapp_flow.description = metadata['description']
                        whatsapp_flow.is_active = metadata.get('is_active', False)
                        whatsapp_flow.save()
                        self.stdout.write('  Flow record updated in database')
                    else:
                        self.stdout.write(self.style.SUCCESS('  Flow record created in database'))
                    
                    # Sync with Meta
                    self.stdout.write('  Syncing with Meta...')
                    success = service.sync_flow(whatsapp_flow, publish=publish)
                    
                    if success:
                        if publish:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Flow synced and published! Flow ID: {whatsapp_flow.flow_id}'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Flow synced as draft! Flow ID: {whatsapp_flow.flow_id}'
                                )
                            )
                            self.stdout.write(
                                self.style.WARNING(
                                    '  Note: Flow is in draft mode. Run with --publish to make it live.'
                                )
                            )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f'  ✗ Sync failed: {whatsapp_flow.sync_error}'
                            )
                        )
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Error processing flow: {str(e)}'
                    )
                )
                import traceback
                self.stdout.write(traceback.format_exc())

        self.stdout.write('\n' + self.style.SUCCESS('Done!'))
