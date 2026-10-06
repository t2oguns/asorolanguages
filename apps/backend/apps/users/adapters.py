from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from .models import UserProfile

class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False  # no email/password signup

class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        data = sociallogin.account.extra_data
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "display_name": data.get("name", "")[:100],
                "avatar_url": data.get("picture") or data.get("avatar_url") or "",
            },
        )
        return user