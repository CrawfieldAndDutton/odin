# KYC Verification API

This is a FastAPI-based project for KYC (Know Your Customer) verification. It includes user authentication, PAN verification, and vehicle RC verification.

![Screenshot (428)](https://github.com/user-attachments/assets/548b19f4-b737-4b12-b6f2-4f214f188317)

## Project Structure

## Setup

1. Clone the repository:

   ```sh
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create a virtual environment and activate it:

   ```sh
   python -m venv odin-env
   source odin-env/bin/activate  # On Windows use `odin-env\Scripts\activate`
   ```

3. Install the dependencies:

   ```sh
   pip install -r requirements.txt
   ```

4. Create a .env
   environment variables:
   ```properties
   RAPID_API_KEY=TOUR_API_KEY
   SECRET_KEY=your_secret_key
   REFRESH_SECRET_KEY=Your_refresh_key
   MONGO_URI="you_mongodb_url"
   MAIN_DB=kyc_fabric_db
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=minutes
   REFRESH_TOKEN_EXPIRE_DAYS=days
   RAZORPAY_KEY_ID=your_razorpay_key_id
   RAZORPAY_KEY_SECRET=your_razorpay_key_secret
   API_BASE_URL=your_api_base_url
   ```

````

## Running the Application

To run the FastAPI application, use the following command:

```sh
uvicorn main:app --reload
````

# Linting

To check the code formatting with flake8, use the following command:

```sh
flake8 .
```

# API Endpoints

## Authentication

`GET /: Welcome message`

`POST /auth/login: User login`

`POST /auth/register: User registration`

`POST /auth/refresh: Refresh access token`

`POST /auth/logout : User Logout`

`GET /users/me : Fetching active user's data`

`PUT /users/me : For update user details`

## KYC Verification

`POST api/v1/pan/verify: PAN verification`

`GET api/v1/rc/verify: Vehicle RC verification`

## Payment

`POST /api/v1/payments/create: Create a payment link for purchasing credits`

`GET /api/v1/payments/verify: Verify a payment from Razorpay callback`

`POST /api/v1/payments/webhook: Handle webhook events from Razorpay`

`GET /api/v1/payments/status/{order_id}: Get the status of a payment`

## Dashboard Payment (User)

`GET /dashboard/api/v1/payments/orders: Get orders for the current user`

`GET /dashboard/api/v1/payments/payments: Get payments for the current user`

`GET /dashboard/api/v1/payments/status/{order_id}: Get the status of a payment`
