# Templates for Razorpay payment service

# Template for dynamic values in payment link creation
RAZORPAY_DYNAMIC_VALUES_TEMPLATE = {
    "amount": 0,  # Will be set to amount * 100 (paise)
    "description": "",  # Will be set to "Purchase of {credits_purchased} credits"
    "customer": {
        "name": "",  # Will be set to user's full name
        "email": "",  # Will be set to user's email
        "contact": ""  # Will be set to user's phone number
    },
    "notes": {
        "user_id": "",  # Will be set to user's ID
        "credits_purchased": ""  # Will be set to credits purchased
    }
}
