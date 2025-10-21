# whatsappcrm_backend/whatsappcrm_backend/urls.py

from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView, TokenBlacklistView
from django.conf import settings
from django.conf.urls.static import static

# Import the custom view to replace the default one
from customer_data.views import MyTokenObtainPairView
# Import the new landing page view
from .views import LandingPageView

urlpatterns = [
    # Landing Page at the root
    path('', LandingPageView.as_view(), name='landing_page'),

    # Django Admin interface - useful for backend management via Jazzmin
    path('admin/', admin.site.urls),
    path('prometheus/', include('django_prometheus.urls')),
    # API endpoints for 'meta_integration' application
    # This includes:
    #   - The webhook receiver for Meta (e.g., /crm-api/meta/webhook/)
    #   - DRF APIs for MetaAppConfig and WebhookEventLog (e.g., /crm-api/meta/api/configs/)
    path('crm-api/meta/', include('meta_integration.urls', namespace='meta_integration_api')),
    
    # API endpoints for 'media_manager' application
    path('crm-api/media/', include('media_manager.urls', namespace='media_manager_api')),
    
    path('crm-api/conversations/', include('conversations.urls', namespace='conversations_api')),
path('crm-api/customer-data/', include('customer_data.urls', namespace='customer_data_api')),
    path('crm-api/stats/', include('stats.urls', namespace='stats_api')),
    path('crm-api/analytics/', include('analytics.urls')),
    # API endpoints for 'flows' application
    # This includes DRF APIs for Flows, FlowSteps, etc. (e.g., /crm-api/flows/flows/)
    path('crm-api/flows/', include('flows.urls', namespace='flows_api')),
    
    # API endpoints for 'customer_data' application (if you add API views to it later)
    # For now, customer_data is primarily managed via the admin and updated by flows.
    # If you need direct API access to CustomerProfile:
    # path('crm-api/customer-data/', include('customer_data.urls', namespace='customer_data_api')),


    # JWT Token Endpoints for authentication from your React Vite frontend
    # Use our custom view to ensure refresh token and user data are returned
    path('crm-api/auth/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # Your frontend will POST to 'token_refresh' with a valid refresh token
    path('crm-api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Optional: Your frontend can POST to 'token_verify' with a token to check its validity
    path('crm-api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # Add the blacklist endpoint to fix 404 on logout
    path('crm-api/auth/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # DRF's built-in login/logout views for the browsable API.
    # These are helpful for testing your APIs directly in the browser during development.
    # They use SessionAuthentication.
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

# --- Serve Media Files in Development ---
# This is not suitable for production. In production, your web server (e.g., Nginx)
# should be configured to serve media files directly.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Note on Namespaces:
# The 'namespace' argument in include() is useful for URL reversing 
# (e.g., using reverse('meta_integration_api:meta_webhook_receiver') in Python code).
# It helps avoid URL name collisions between apps.
