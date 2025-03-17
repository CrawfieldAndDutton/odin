from mongoengine.queryset.visitor import Q

from models.user_model import VerifiedUserInformation


class VerifiedUserInformationRepository:

    def get_user_by_email_or_phone_number(self, email: str, phone_number: str):
        return VerifiedUserInformation.objects(Q(email=email) | Q(phone_number=phone_number)).first()

    @staticmethod
    def create_verified_user_information(email: str, phone_number: str, otp: str):

        # Create new user if doesn't exist
        user = VerifiedUserInformation(email=email, phone_number=phone_number, otp=otp)
        user.save()
        return user

    @staticmethod
    def find_user_by_email(email: str):
        return VerifiedUserInformation.objects(email=email).first()
