# ▶️ Usage

Once you have completed the installation and configuration steps, you can run the application and perform tests.

## Running the Application

To start the development server, run the following command from the root of the project directory:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

## Running Tests

This project uses `pytest` for testing. To run the full test suite, use the following command:

```bash
pytest
```

Ensure you have a separate test database or have configured your environment appropriately to run tests without affecting your development data.
