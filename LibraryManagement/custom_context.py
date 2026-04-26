from django.conf import settings


def ai_service_context(request):
    return {
        "AI_SERVICE_URL": getattr(settings, "AI_SERVICE_URL", ""),
        "AI_SERVICE_CONTEXT": getattr(settings, "AI_SERVICE_CONTEXT", {}),
    }
