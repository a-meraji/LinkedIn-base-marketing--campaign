from django.urls import path
from .views import (
    # Frontend Views
    DashboardView,
    ScrapingPageView,
    EmailCampaignPageView,
    WhatsAppCampaignPageView,
    TaskTrackerPageView,
    # API Views
    StartScrapingView,
    StartEmailCampaignView,
    StartWhatsappCampaignView,
    TaskStatusView
)

urlpatterns = [
    # ==========================================
    # FRONTEND PAGES
    # ==========================================
    path('', DashboardView.as_view(), name='dashboard'),
    path('scraping', ScrapingPageView.as_view(), name='scraping-page'),
    path('emailCampaign', EmailCampaignPageView.as_view(), name='email-campaign-page'),
    path('whatsappCampaign', WhatsAppCampaignPageView.as_view(), name='whatsapp-campaign-page'),
    path('taskTracker', TaskTrackerPageView.as_view(), name='task-tracker-page'),
    
    # ==========================================
    # API ENDPOINTS
    # ==========================================
    # API Endpoint #1: Start the scraping and data collection process
    path('startScraping', StartScrapingView.as_view(), name='start-scraping'),

    # API Endpoint #2: Start the email outreach campaign
    path('startEmailCampaign', StartEmailCampaignView.as_view(), name='start-email-campaign'),

    # API Endpoint #3: Start the WhatsApp outreach campaign
    path('startWhatsappCampaign', StartWhatsappCampaignView.as_view(), name='start-whatsapp-campaign'),

    # API Endpoint: Check the status of any running task (scraping, email, or WhatsApp)
    path('taskStatus/<str:task_id>', TaskStatusView.as_view(), name='task-status'),
]
