from mongoengine.queryset.visitor import Q

from models.user_model import VerifiedUserInformation


class VerifiedUserInformationRepository:
    @staticmethod
    def create_user_otp(email: str, phone_number: str, otp: str):
        # Check if user already exists
        existing_user = VerifiedUserInformation.objects.filter(Q(email=email) | Q(phone_number=phone_number)).first()
        if existing_user:
            # Update the OTP and phone_number for existing user
            existing_user.otp = otp
            existing_user.phone_number = phone_number  # Update phone_number number
            existing_user.is_email_verified = False  # Reset verification status
            existing_user.save()
            return existing_user
        else:
            # Create new user if doesn't exist
            user = VerifiedUserInformation(email=email, phone_number=phone_number, otp=otp)
            user.save()
            return user

    @staticmethod
    def find_user_by_email(email: str):
        return VerifiedUserInformation.objects(email=email).first()

    @staticmethod
    def verify_user(email: str, otp: str):
        user = VerifiedUserInformation.objects(email=email, otp=otp).first()
        if user:
            user.is_email_verified = True
            user.save()
        return user
