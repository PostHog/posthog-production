from posthog.urls import urlpatterns as posthog_urls, home
from django.urls import path, re_path
from django.contrib.auth import decorators
from multi_tenancy.views import (
    signup_view,
    user_with_billing,
    stripe_checkout_view,
    stripe_billing_portal,
    billing_welcome_view,
    billing_failed_view,
    billing_hosted_view,
    stripe_webhook,
)


urlpatterns = posthog_urls[:-1]
urlpatterns[5] = path(
    "api/user/", user_with_billing
)  # Override to include billing information


urlpatterns += [
    path("signup", signup_view, name="signup"),
    path(
        "billing/setup", stripe_checkout_view, name="billing_setup"
    ),  # Redirect to Stripe Checkout to set-up billing (requires session ID)
    path(
        "billing/manage", stripe_billing_portal, name="billing_manage"
    ),  # Redirect to Stripe Customer Portal to manage subscription
    path(
        "billing/welcome", billing_welcome_view, name="billing_welcome"
    ),  # Page with success message after setting up billing
    path(
        "billing/failed", billing_failed_view, name="billing_failed"
    ),  # Page with failure message after attempting to set up billing
    path(
        "billing/hosted", billing_hosted_view, name="billing_hosted"
    ),  # Page with success message after setting up billing for hosted plans
    path(
        "billing/stripe_webhook", stripe_webhook, name="billing_stripe_webhook"
    ),  # Stripe Webhook
    re_path(r"^.*", decorators.login_required(home)),
]
