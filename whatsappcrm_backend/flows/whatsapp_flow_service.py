# whatsappcrm_backend/flows/whatsapp_flow_service.py

import requests
import json
import logging
from typing import Optional, Dict, Any
from django.utils import timezone
from django.conf import settings

from .models import WhatsAppFlow, WhatsAppFlowResponse
from meta_integration.models import MetaAppConfig
from conversations.models import Contact

logger = logging.getLogger(__name__)


class WhatsAppFlowService:
    """
    Service for managing WhatsApp interactive flows with Meta's API.
    Handles creation, updating, publishing, and syncing flows with Meta.
    """
    
    def __init__(self, meta_config: MetaAppConfig):
        """
        Initialize the service with a Meta app configuration.
        
        Args:
            meta_config: The MetaAppConfig instance to use for API calls
        """
        self.meta_config = meta_config
        self.base_url = f"https://graph.facebook.com/{meta_config.api_version}"
        self.headers = {
            "Authorization": f"Bearer {meta_config.access_token}",
            "Content-Type": "application/json",
        }
    
    def create_flow(self, whatsapp_flow: WhatsAppFlow) -> bool:
        """
        Creates a new flow on Meta's platform.
        
        Args:
            whatsapp_flow: The WhatsAppFlow instance to create on Meta
            
        Returns:
            bool: True if successful, False otherwise
        """
        url = f"{self.base_url}/{self.meta_config.waba_id}/flows"
        
        # Get the version suffix from settings
        version_suffix = getattr(settings, 'META_SYNC_VERSION_SUFFIX', 'v1.02')
        
        # Append version suffix to flow name
        flow_name = whatsapp_flow.friendly_name or whatsapp_flow.name
        flow_name_with_version = f"{flow_name}_{version_suffix}"
        
        payload = {
            "name": flow_name_with_version,
            "categories": ["OTHER"]  # Default category, can be made configurable
        }
        
        try:
            whatsapp_flow.sync_status = 'syncing'
            whatsapp_flow.save(update_fields=['sync_status'])
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=20)
            response.raise_for_status()
            
            result = response.json()
            flow_id = result.get('id')
            
            if flow_id:
                whatsapp_flow.flow_id = flow_id
                whatsapp_flow.sync_status = 'draft'
                whatsapp_flow.last_synced_at = timezone.now()
                whatsapp_flow.sync_error = None
                whatsapp_flow.save()
                
                logger.info(f"Successfully created flow on Meta with ID: {flow_id}")
                
                # Now update the flow JSON
                return self.update_flow_json(whatsapp_flow)
            else:
                raise ValueError("No flow ID returned from Meta API")
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error creating flow on Meta: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f" - Details: {error_details}"
                except:
                    error_msg += f" - Response: {e.response.text}"
            
            logger.error(error_msg)
            whatsapp_flow.sync_status = 'error'
            whatsapp_flow.sync_error = error_msg
            whatsapp_flow.save()
            return False
        except Exception as e:
            error_msg = f"Unexpected error creating flow: {e}"
            logger.error(error_msg, exc_info=True)
            whatsapp_flow.sync_status = 'error'
            whatsapp_flow.sync_error = error_msg
            whatsapp_flow.save()
            return False
    
    def update_flow_json(self, whatsapp_flow: WhatsAppFlow) -> bool:
        """
        Updates the flow JSON definition on Meta's platform.
        
        Args:
            whatsapp_flow: The WhatsAppFlow instance with updated JSON
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not whatsapp_flow.flow_id:
            logger.error(f"Cannot update flow JSON: Flow {whatsapp_flow.name} has no flow_id")
            return False
        
        url = f"{self.base_url}/{whatsapp_flow.flow_id}/assets"
        
        # Prepare the file data for multipart/form-data upload
        flow_json_str = json.dumps(whatsapp_flow.flow_json)
        
        # Create multipart form data with the file parameter
        files = {
            'file': ('flow.json', flow_json_str, 'application/json')
        }
        
        data = {
            "name": "flow.json",
            "asset_type": "FLOW_JSON"
        }
        
        # Create headers without Content-Type (requests will set it for multipart)
        headers = {
            "Authorization": f"Bearer {self.meta_config.access_token}"
        }
        
        try:
            whatsapp_flow.sync_status = 'syncing'
            whatsapp_flow.save(update_fields=['sync_status'])
            
            response = requests.post(url, headers=headers, data=data, files=files, timeout=20)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                whatsapp_flow.sync_status = 'draft'
                whatsapp_flow.last_synced_at = timezone.now()
                whatsapp_flow.sync_error = None
                whatsapp_flow.save()
                
                logger.info(f"Successfully updated flow JSON for flow ID: {whatsapp_flow.flow_id}")
                return True
            else:
                raise ValueError(f"Flow JSON update failed: {result}")
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error updating flow JSON: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f" - Details: {error_details}"
                except:
                    error_msg += f" - Response: {e.response.text}"
            
            logger.error(error_msg)
            whatsapp_flow.sync_status = 'error'
            whatsapp_flow.sync_error = error_msg
            whatsapp_flow.save()
            return False
        except Exception as e:
            error_msg = f"Unexpected error updating flow JSON: {e}"
            logger.error(error_msg, exc_info=True)
            whatsapp_flow.sync_status = 'error'
            whatsapp_flow.sync_error = error_msg
            whatsapp_flow.save()
            return False
    
    def publish_flow(self, whatsapp_flow: WhatsAppFlow) -> bool:
        """
        Publishes a flow on Meta's platform, making it available for use.
        
        Args:
            whatsapp_flow: The WhatsAppFlow instance to publish
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not whatsapp_flow.flow_id:
            logger.error(f"Cannot publish flow: Flow {whatsapp_flow.name} has no flow_id")
            return False
        
        url = f"{self.base_url}/{whatsapp_flow.flow_id}/publish"
        
        try:
            whatsapp_flow.sync_status = 'syncing'
            whatsapp_flow.save(update_fields=['sync_status'])
            
            response = requests.post(url, headers=self.headers, json={}, timeout=20)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                whatsapp_flow.sync_status = 'published'
                whatsapp_flow.last_synced_at = timezone.now()
                whatsapp_flow.sync_error = None
                whatsapp_flow.save()
                
                logger.info(f"Successfully published flow ID: {whatsapp_flow.flow_id}")
                return True
            else:
                raise ValueError(f"Flow publish failed: {result}")
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error publishing flow: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_msg += f" - Details: {error_details}"
                except:
                    error_msg += f" - Response: {e.response.text}"
            
            logger.error(error_msg)
            whatsapp_flow.sync_status = 'error'
            whatsapp_flow.sync_error = error_msg
            whatsapp_flow.save()
            return False
        except Exception as e:
            error_msg = f"Unexpected error publishing flow: {e}"
            logger.error(error_msg, exc_info=True)
            whatsapp_flow.sync_status = 'error'
            whatsapp_flow.sync_error = error_msg
            whatsapp_flow.save()
            return False
    
    def sync_flow(self, whatsapp_flow: WhatsAppFlow, publish: bool = False) -> bool:
        """
        Syncs a flow with Meta - creates if new, updates if exists.
        Optionally publishes the flow.
        
        Args:
            whatsapp_flow: The WhatsAppFlow instance to sync
            publish: Whether to publish the flow after syncing
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not whatsapp_flow.flow_id:
            # Flow doesn't exist on Meta yet, create it
            success = self.create_flow(whatsapp_flow)
        else:
            # Flow exists, update it
            success = self.update_flow_json(whatsapp_flow)
        
        if success and publish:
            return self.publish_flow(whatsapp_flow)
        
        return success
    
    def get_flow_details(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves flow details from Meta's API.
        
        Args:
            flow_id: The flow ID on Meta's platform
            
        Returns:
            dict: Flow details or None if error
        """
        url = f"{self.base_url}/{flow_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Retrieved flow details for flow ID: {flow_id}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving flow details: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    logger.error(f"Error details: {error_details}")
                except:
                    logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving flow details: {e}", exc_info=True)
            return None
    
    @staticmethod
    def create_flow_message_data(flow_id: str, screen: str = "WELCOME", 
                                   flow_cta: str = "Continue",
                                   header_text: Optional[str] = None,
                                   body_text: Optional[str] = None,
                                   footer_text: Optional[str] = None,
                                   flow_token: Optional[str] = None) -> dict:
        """
        Creates the message payload for sending a WhatsApp Flow as an interactive message.
        
        Args:
            flow_id: The flow ID from Meta
            screen: The initial screen to show (default: "WELCOME")
            flow_cta: The call-to-action button text
            header_text: Optional header text
            body_text: Optional body text
            footer_text: Optional footer text
            flow_token: Optional flow token for tracking
            
        Returns:
            dict: The message payload for WhatsApp API
        """
        interactive_payload = {
            "type": "flow",
            "body": {"text": body_text or "Please complete the form"},
            "action": {
                "name": "flow",
                "parameters": {
                    "flow_message_version": "3",
                    "flow_token": flow_token or "",
                    "flow_id": flow_id,
                    "flow_cta": flow_cta,
                    "flow_action": "navigate",
                    "flow_action_payload": {
                        "screen": screen
                    }
                }
            }
        }
        
        if header_text:
            interactive_payload["header"] = {"type": "text", "text": header_text}
        
        if footer_text:
            interactive_payload["footer"] = {"text": footer_text}
        
        return interactive_payload
    
    @staticmethod
    def process_flow_response(response_data: Dict[str, Any], contact: Contact, 
                               whatsapp_flow: WhatsAppFlow) -> WhatsAppFlowResponse:
        """
        Processes and stores a flow response from a user.
        
        Args:
            response_data: The response payload from Meta webhook
            contact: The contact who submitted the response
            whatsapp_flow: The WhatsApp flow instance
            
        Returns:
            WhatsAppFlowResponse: The created response instance
        """
        flow_token = response_data.get('flow_token', '')
        
        flow_response = WhatsAppFlowResponse.objects.create(
            whatsapp_flow=whatsapp_flow,
            contact=contact,
            flow_token=flow_token,
            response_data=response_data,
            is_processed=False
        )
        
        logger.info(f"Created flow response {flow_response.id} for contact {contact.id}")
        return flow_response
