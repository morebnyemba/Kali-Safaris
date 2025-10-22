# whatsappcrm_backend/flows/utils.py
import logging
from jinja2 import Environment, select_autoescape, Undefined

from conversations.models import Contact

logger = logging.getLogger(__name__)

# --- Jinja2 Environment Setup ---
class SilentUndefined(Undefined):
    def _fail_with_undefined_error(self, *args, **kwargs):
        return ''

jinja_env = Environment(
    loader=None,
    autoescape=select_autoescape(['html', 'xml'], disabled_extensions=('txt',), default_for_string=False),
    undefined=SilentUndefined,
    enable_async=False
)

def get_contact_from_context(context: dict) -> Contact | None:
    """
    Safely retrieves the Contact object from the flow context.
    """
    contact = context.get('contact')
    if not contact or not isinstance(contact, Contact):
        logger.error("Could not find a valid 'contact' object in the flow context.")
        return None
    return contact

def render_string_with_context(template_string: str, context: dict) -> str:
    """
    Renders a Jinja2 template string with the provided context.
    """
    if not isinstance(template_string, str):
        return template_string

    try:
        template = jinja_env.from_string(template_string)
        # The full context is passed to the template for rendering.
        return template.render(context)
    except Exception as e:
        logger.error(f"Jinja2 template rendering failed: {e}. Template: '{template_string}'", exc_info=False)
        return template_string