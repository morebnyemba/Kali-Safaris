"Meta Catalog Service for syncing products with Meta (Facebook) Product Catalog.

IMPORTANT: Image URL Accessibility
===================================
For products to be successfully created in Meta's catalog, the image_link URL must be:
1. Publicly accessible (no authentication required)
2. Reachable from Meta's servers (not behind a firewall/VPN)
3. Return a valid image with proper Content-Type header
4. Use HTTPS protocol or be a data URI

Meta API requires the image_link field for all products (error #10801). When a product 
has no images, a transparent 1x1 pixel PNG data URI is used as a placeholder. This ensures
the product can be created in Meta's catalog without requiring external infrastructure.

Infrastructure Requirements for Product Images:
- Media files must be properly served by nginx or another web server
- The docker-compose.yml should include a shared volume for media files
- Nginx configuration should serve media files from the correct path

Example nginx configuration:
    location /media/ {
        alias /srv/www/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

Example docker-compose volume:
    backend:
        volumes:
            - media_files:/app/mediafiles
    nginx:
        volumes:
            - media_files:/srv/www/media:ro

Django Settings:
- BACKEND_DOMAIN_FOR_CSP: Domain name for constructing absolute URLs (e.g., 'backend.hanna.co.zw')

Placeholder Image:
When a product has no images, a transparent 1x1 pixel PNG data URI is used automatically.
This ensures Meta API compliance without requiring external resources or infrastructure.

If image URLs are not accessible, Meta will reject product creation with a 400 error.
"

import requests
import logging
import json
from django.conf import settings
from .models import MetaAppConfig
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Transparent 1x1 pixel PNG as a data URI for products without images
# This is used as a placeholder to satisfy Meta API's requirement for image_link field
PLACEHOLDER_IMAGE_DATA_URI = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


class MetaCatalogService:
    def __init__(self):
        try:
            active_config = MetaAppConfig.objects.get_active_config()
            self.api_version = active_config.api_version
            self.access_token = active_config.access_token
            self.catalog_id = active_config.catalog_id
        except MetaAppConfig.DoesNotExist:
            # Handle case where no active config is found
            self.api_version = "v18.0" # Default or fallback
            self.access_token = None
            self.catalog_id = None

        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def _get_headers(self):
        if not self.access_token:
            raise ValueError("Meta access token is not configured.")
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _get_product_data(self, product):
        """
        Constructs a robust product data payload from a Product instance,
        omitting fields that are null or empty to prevent '400 Bad Request' errors.
        
        Reference: https://developers.facebook.com/docs/marketing-api/catalog
        
        Required fields per Meta API:
        - retailer_id: Unique product identifier (mapped from SKU)
        - name: Product name
        - availability: in stock | out of stock | available for order
        - condition: new | refurbished | used
        - price: Price as integer in cents/minor currency units (e.g., 10000 for $100.00)
        - currency: ISO 4217 currency code (e.g., "USD")
        - link: Product URL
        - image_link: URL to product image (must be absolute URL and publicly accessible)
                     Note: Meta API error #10801 "(#10801) \"image_url\" must be specified."
                     requires this field (despite the error message saying "image_url", the 
                     actual field name is "image_link"). A placeholder image URL is used 
                     when the product has no images.
        
        Optional fields:
        - description: Product description
        - brand: Brand name
        """
        # SKU is mandatory for the retailer_id
        if not product.sku:
            raise ValueError(f"Product '{product.name}' (ID: {product.id}) is missing an SKU, which is required for 'retailer_id'.")

        # Format price correctly - Meta expects an integer in cents (minor currency units)
        # For USD: $100.00 = 10000 cents
        price_value = 0
        if product.price is not None:
            # Convert to cents by multiplying by 100 and rounding to nearest integer
            price_value = int(round(float(product.price) * 100))

        data = {
            "retailer_id": product.sku,
            "name": product.name,
            "price": price_value,  # Integer in cents
            "currency": product.currency,
            "condition": "new",
            "availability": "in stock" if product.stock_quantity > 0 else "out of stock",
            # Provide a default link if not set, as it's often required.
            "link": product.website_url or "https://www.hanna-installations.com/product-not-available"
        }

        # Add optional description if present
        if product.description:
            data["description"] = product.description

        # Add optional brand if present
        if product.brand:
            data["brand"] = product.brand

        # Get the first image URL, if available
        # Meta API requires absolute URLs, not relative paths
        # IMPORTANT: The URL must be publicly accessible for Meta's servers to fetch
        # Meta API now requires image_link field to be present
        # Error #10801: "(#10801) \"image_url\" must be specified."
        
        # Get the backend domain once to avoid duplication
        backend_domain = getattr(settings, 'BACKEND_DOMAIN_FOR_CSP', 'backend.hanna.co.zw')
        
        first_image = product.images.first()
        # Check if image exists and has a truthy URL value (not None)
        if first_image and hasattr(first_image.image, 'url') and first_image.image.url:
            # Strip whitespace and ensure string type for further validation
            image_url = str(first_image.image.url).strip()
            
            # Validate that URL is non-empty after stripping whitespace
            if image_url:
                # If the URL is relative, convert it to absolute
                if image_url.startswith('/'):
                    # Use https as the application is behind an HTTPS proxy
                    image_url = f"https://{backend_domain}{image_url}"
                
                data["image_link"] = image_url
                logger.debug(f"Product image URL for Meta: {image_url}")
            else:
                # URL was only whitespace - use placeholder
                data["image_link"] = PLACEHOLDER_IMAGE_DATA_URI
                logger.warning(
                    f"Product '{product.name}' (ID: {product.id}) has image with whitespace-only URL. "
                    f"Using transparent placeholder data URI for Meta Catalog compliance."
                )
        else:
            # Meta API requires image_link field even when no image is available
            # Use a transparent 1x1 pixel PNG as a data URI - this is always accessible
            # and doesn't require any external resources or infrastructure
            data["image_link"] = PLACEHOLDER_IMAGE_DATA_URI
            logger.warning(
                f"Product '{product.name}' (ID: {product.id}) has no images or empty image URL. "
                f"Using transparent placeholder data URI for Meta Catalog compliance."
            )

        return data

    def create_product_in_catalog(self, product):
        if not self.catalog_id:
            raise ValueError("WhatsApp Catalog ID is not configured.")
        url = f"{self.base_url}/{self.catalog_id}/products"
        data = self._get_product_data(product)
        
        logger.info(f"Creating product in Meta Catalog: {product.name} (SKU: {product.sku})")
        logger.debug(f"Payload: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
        
        # Log the full response for debugging
        try:
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully created product in catalog. Response: {result}")
            return result
        except requests.exceptions.HTTPError as e:
            # Log the full error response from Meta
            error_details = {}
            try:
                error_details = response.json()
                error_body = json.dumps(error_details, indent=2)
                
                # Extract useful error information
                error_message = error_details.get('error', {}).get('message', str(error_details))
                error_code = error_details.get('error', {}).get('code', response.status_code)
                error_type = error_details.get('error', {}).get('type', 'Unknown')
                
                logger.error(
                    f"═══════════════════════════════════════════════════════\n"
                    f"META API ERROR - Product Creation Failed\n"
                    f"═══════════════════════════════════════════════════════\n"
                    f"Product: {product.name} (ID: {product.id}, SKU: {product.sku})\n"
                    f"Error Code: {error_code}\n"
                    f"Error Type: {error_type}\n"
                    f"Error Message: {error_message}\n"
                    f"HTTP Status: {response.status_code}\n"
                    f"Full Response:\n{error_body}\n"
                    f"═══════════════════════════════════════════════════════"
                )
                
                # Check if the error is related to image_link
                if 'image' in error_message.lower() and 'image_link' in data:
                    logger.error(
                        f"⚠ IMAGE URL ISSUE DETECTED ⚠\n"
                        f"Image URL: {data['image_link']}\n"
                        f"This URL must be publicly accessible to Meta's servers.\n"
                        f"Test accessibility with: curl -I {data['image_link']}\n"
                        f"Ensure nginx/NPM is properly serving media files and the URL is not behind auth."
                    )
                
                # Re-raise with more context
                raise ValueError(
                    f"Meta API Error ({error_code}): {error_message}. "
                    f"Check logs for full details."
                ) from e
                
            except (ValueError, KeyError, json.JSONDecodeError):
                # If we can't parse the JSON error response
                error_body = response.text
                logger.error(
                    f"═══════════════════════════════════════════════════════\n"
                    f"META API ERROR - Product Creation Failed (Raw Response)\n"
                    f"═══════════════════════════════════════════════════════\n"
                    f"Product: {product.name} (ID: {product.id}, SKU: {product.sku})\n"
                    f"HTTP Status: {response.status_code}\n"
                    f"Response Body:\n{error_body}\n"
                    f"═══════════════════════════════════════════════════════"
                )
                raise ValueError(
                    f"Meta API Error (HTTP {response.status_code}): {error_body[:200]}..."
                ) from e
        except requests.exceptions.Timeout:
            error_msg = "Request to Meta API timed out after 30 seconds"
            logger.error(f"{error_msg} for product '{product.name}' (SKU: {product.sku})")
            raise ValueError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error connecting to Meta API: {str(e)}"
            logger.error(f"{error_msg} for product '{product.name}' (SKU: {product.sku})")
            raise ValueError(error_msg) from e

    def update_product_in_catalog(self, product):
        if not product.whatsapp_catalog_id:
            raise ValueError("Product does not have a WhatsApp Catalog ID.")
        
        url = f"{self.base_url}/{product.whatsapp_catalog_id}"
        data = self._get_product_data(product)
        
        logger.info(f"Updating product in Meta Catalog: {product.name} (Catalog ID: {product.whatsapp_catalog_id})")
        logger.debug(f"Payload: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
        
        # Log the full response for debugging
        try:
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully updated product in catalog. Response: {result}")
            return result
        except requests.exceptions.HTTPError as e:
            # Log the full error response from Meta
            error_details = {}
            try:
                error_details = response.json()
                error_body = json.dumps(error_details, indent=2)
                
                # Extract useful error information
                error_message = error_details.get('error', {}).get('message', str(error_details))
                error_code = error_details.get('error', {}).get('code', response.status_code)
                error_type = error_details.get('error', {}).get('type', 'Unknown')
                
                logger.error(
                    f"═══════════════════════════════════════════════════════\n"
                    f"META API ERROR - Product Update Failed\n"
                    f"═══════════════════════════════════════════════════════\n"
                    f"Product: {product.name} (ID: {product.id}, Catalog ID: {product.whatsapp_catalog_id})\n"
                    f"Error Code: {error_code}\n"
                    f"Error Type: {error_type}\n"
                    f"Error Message: {error_message}\n"
                    f"HTTP Status: {response.status_code}\n"
                    f"Full Response:\n{error_body}\n"
                    f"═══════════════════════════════════════════════════════"
                )
                
                # Check if the error is related to image_link
                if 'image' in error_message.lower() and 'image_link' in data:
                    logger.error(
                        f"⚠ IMAGE URL ISSUE DETECTED ⚠\n"
                        f"Image URL: {data['image_link']}\n"
                        f"This URL must be publicly accessible to Meta's servers."
                    )
                
                # Re-raise with more context
                raise ValueError(
                    f"Meta API Error ({error_code}): {error_message}. "
                    f"Check logs for full details."
                ) from e
                
            except (ValueError, KeyError, json.JSONDecodeError):
                # If we can't parse the JSON error response
                error_body = response.text
                logger.error(
                    f"═══════════════════════════════════════════════════════\n"
                    f"META API ERROR - Product Update Failed (Raw Response)\n"
                    f"═══════════════════════════════════════════════════════\n"
                    f"Product: {product.name} (ID: {product.id}, Catalog ID: {product.whatsapp_catalog_id})\n"
                    f"HTTP Status: {response.status_code}\n"
                    f"Response Body:\n{error_body}\n"
                    f"═══════════════════════════════════════════════════════"
                )
                raise ValueError(
                    f"Meta API Error (HTTP {response.status_code}): {error_body[:200]}..."
                ) from e
        except requests.exceptions.Timeout:
            error_msg = "Request to Meta API timed out after 30 seconds"
            logger.error(f"{error_msg} for product '{product.name}' (Catalog ID: {product.whatsapp_catalog_id})")
            raise ValueError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error connecting to Meta API: {str(e)}"
            logger.error(f"{error_msg} for product '{product.name}' (Catalog ID: {product.whatsapp_catalog_id})")
            raise ValueError(error_msg) from e

    def delete_product_from_catalog(self, product):
        if not product.whatsapp_catalog_id:
            raise ValueError("Product does not have a WhatsApp Catalog ID.")
        
        url = f"{self.base_url}/{product.whatsapp_catalog_id}"
        
        logger.info(f"Deleting product from Meta Catalog: {product.name} (Catalog ID: {product.whatsapp_catalog_id})")
        
        response = requests.delete(url, headers=self._get_headers())
        
        # Log the full response for debugging
        try:
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully deleted product from catalog. Response: {result}")
            return result
        except requests.exceptions.HTTPError as e:
            # Log the full error response from Meta
            error_body = ""
            error_details = {}
            try:
                error_details = response.json()
                error_body = json.dumps(error_details, indent=2)
                logger.error(
                    f"Meta API error response when deleting product '{product.name}' (Catalog ID: {product.whatsapp_catalog_id}):\n"
                    f"Status Code: {response.status_code}\n"
                    f"Error Details: {error_body}"
                )
            except Exception:
                error_body = response.text
                logger.error(
                    f"Meta API error response (raw) when deleting product '{product.name}' (Catalog ID: {product.whatsapp_catalog_id}):\n"
                    f"Status Code: {response.status_code}\n"
                    f"Response: {error_body}"
                )
            raise