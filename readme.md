# PAN Validation API

This is a FastAPI-based application for validating PAN numbers through an external API and storing the results in a MongoDB database.

## Requirements

- Python 3.12.3
- MongoDB

## Installation

1. Clone the repository:

```sh
git clone <repository-url>
cd odin
```

## 1 Create and activate a virtual environment:

python -m venv cd-env
source cd-env/Scripts/activate # On Windows
source cd-env/bin/activate # On Unix or MacOS

## 2 Install the dependencies:

pip install -r requirements.txt

## 3 Create a .env file in the root directory and add the following environment variables:

PAN_API_KEY=<your_pan_api_key>
MONGODB_URI=<your_mongodb_uri>

# Running the Application

`uvicorn app.main:app --reload`

`The application will be available at http://127.0.0.1:8000.`
`Swagger UI http://127.0.0.1:8000/docs`

# API Routes

Validate PAN
`URL: /api/v1/validate-pan`
`Method: POST`
Request Body:

```json
{
	"pan": "ABCDE1234F"
}
```

Response:

```json
{
"txn_id": "unique_transaction_id",
"status": "success",
"message": "PAN validated successfully",
"status_code": 200,
"result": {
"pan_status": "valid",
"pan_type": "individual",
"pan": "ABCDE1234F",
"full_name": "John Doe"
}
```

Get PAN History
`URL: /api/v1/pan-history/{pan}`
`Method: GET`
Response:

```json
{
	"history": [
		{
			"txn_id": "unique_transaction_id",
			"status": "success",
			"message": "PAN validated successfully",
			"status_code": 200,
			"pan_status": "valid",
			"pan_type": "individual",
			"pan": "ABCDE1234F",
			"full_name": "John Doe",
			"created_at": "2023-10-01T00:00:00Z"
		}
	]
}
```

# Project Structure

odin/
├── .env
├── .flake8
├── .github/
│ └── workflows/
│ └── ci.yml
├── .gitignore
├── .idea/
│ └── ...
├── app/
│ ├── **init**.py
│ ├── api/
│ │ ├── **init**.py
│ │ └── endpoints/
│ │ ├── **init**.py
│ │ └── pan_validation.py
│ ├── config.py
│ ├── core/
│ │ ├── **init**.py
│ │ └── database.py
│ ├── main.py
│ ├── models/
│ │ ├── **init**.py
│ │ └── pan_validation.py
│ ├── schemas/
│ │ ├── **init**.py
│ │ └── pan_validation.py
│ └── services/
│ ├── **init**.py
│ └── pan_validation_service.py
├── cd-env/
│ └── ...
├── requirements.txt
└── .gitignore

# Running Tests

Uncomment the test steps in the ci.yml file to enable running tests with pytest.

      - name: Run tests with pytest
       run: |
                 pytest --maxfail=1 --disable-warnings -q  # Run the tests with pytest and set options

# Linting Lint the code using flake8:

flake8 .
