# whatsappcrm_backend/conversations/services.py

import logging
from .models import Contact
from meta_integration.models import MetaAppConfig # Keep for type hinting, even if not used directly on model

logger = logging.getLogger(__name__)

def get_or_create_contact_by_wa_id(wa_id: str, name: str = None, meta_app_config: MetaAppConfig = None):
    """
    Retrieves or creates a Contact based on their WhatsApp ID.
    Updates the name if a new one is provided for an existing contact.
    """
    if not wa_id:
        logger.error("get_or_create_contact_by_wa_id called with an empty wa_id. Cannot proceed.")
        return None, False # The calling code should handle this possibility

    # Prepare defaults for creation. Only 'name' is updated if it exists.
    defaults = {}
    if name:
        defaults['name'] = name
    
    # The 'associated_app_config' field on the Contact model is currently commented out.
    # If you uncomment it, you can use the meta_app_config parameter like this:
    if meta_app_config:
        defaults['associated_app_config'] = meta_app_config

    contact, created = Contact.objects.update_or_create(
        whatsapp_id=wa_id,
        defaults=defaults
    )

    if created:
        logger.info(f"Created new contact: {name or 'Unknown'} ({wa_id})")
    else:
        # This part is useful if the user's WhatsApp name changes and you want to update it.
        # We only update if the new name is different from the old one to avoid unnecessary DB writes.
        if name and contact.name != name:
            logger.info(f"Updating contact name for {wa_id} from '{contact.name}' to '{name}'.")
            contact.name = name
            # last_seen is auto_now, so it will be updated automatically on save.
            contact.save(update_fields=['name'])

    return contact, created