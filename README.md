# ZERO-COMP Solar Weather API

![GitHub last commit](https://img.shields.io/github/last-commit/your-username/your-repo)
![GitHub issues](https://img.shields.io/github/issues/your-username/your-repo)
![GitHub pull requests](https://img.shields.io/github/issues-pr/your-username/your-repo)
![GitHub license](https://img.shields.io/github/license/your-username/your-repo)

**ZERO-COMP** is a real-time, enterprise-grade solar flare prediction API powered by NASA-IBM's groundbreaking **Surya-1.0** transformer model. This platform provides critical solar weather forecasting to industries dependent on space and atmospheric reliability, such as satellite operators, power grid companies, and aviation firms.

Our mission is to deliver actionable, high-accuracy solar weather intelligence through a robust and scalable platform. By offering tiered access via web dashboards, REST APIs, and real-time WebSocket alerts, ZERO-COMP empowers customers to mitigate operational risks, protect valuable assets, and ensure safety during significant solar events.

## ✨ Key Features

- **Real-Time Solar Flare Prediction:** Leverages the Surya-1.0 model to deliver solar flare predictions with updates every 10 minutes.
- **Multi-Tiered Access:** Offers `Free`, `Pro`, and `Enterprise` subscription tiers to cater to different user needs.
- **REST API & WebSocket Alerts:** Provides a comprehensive REST API and real-time WebSocket notifications.
- **Developer-Friendly:** Built with a modern, scalable architecture and provides interactive API documentation.
- **Comprehensive Dashboard:** A Next.js-based frontend for real-time visualization of solar activity.

## 🏛️ System Architecture

The ZERO-COMP platform is designed with a modern, microservices-based architecture to ensure scalability, reliability, and maintainability.

```mermaid
graph TB
    subgraph "External Services"
        NASA[NASA Solar Data Sources]
        Surya[Surya-1.0 Model<br/>Hugging Face]
        Razorpay[Razorpay Payment Processing]
    end

    subgraph "Core Platform"
        subgraph "Backend Services"
            API[FastAPI Backend<br/>REST + WebSocket]
            Scheduler[Prediction Scheduler<br/>10-minute intervals]
            Inference[Model Inference Engine]
        end

        subgraph "Data Layer"
            DB[(Supabase PostgreSQL<br/>Predictions + Users)]
            Auth[Supabase Auth<br/>JWT + Session Management]
        end

        subgraph "Frontend"
            Dashboard[Next.js Dashboard<br/>Real-time Visualization]
        end
    end

    subgraph "Clients"
        WebClients[Web Dashboard Users]
        APIClients[API Integration Clients<br/>Satellites, Aviation, Power Grid]
        WSClients[WebSocket Subscribers<br/>Real-time Alerts]
    end

    NASA --> Scheduler
    Scheduler --> Inference
    Inference --> Surya
    Inference --> DB
    API --> DB
    API --> Auth
    Dashboard --> API
    Dashboard --> Auth

    WebClients --> Dashboard
    APIClients --> API
    WSClients --> API

    Auth --> Razorpay
```

## 💻 Technology Stack

- **Backend**: FastAPI (Python 3.9+) with Uvicorn ASGI server
- **Database**: Supabase (PostgreSQL) with real-time subscriptions
- **Authentication**: Supabase Auth with JWT tokens
- **ML Model**: NASA-IBM Surya-1.0 via Hugging Face Transformers
- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Real-time**: WebSocket connections via FastAPI + Supabase Realtime
- **Payments**: Razorpay integration for subscription management
- **Deployment**: Railway/Fly.io (backend), Vercel (frontend)

## 🚀 Getting Started

This guide will walk you through setting up the ZERO-COMP Solar Weather API on your local machine for development and testing.

### Prerequisites

Before you begin, ensure you have the following installed:
- [Python](https.python.org/downloads/) (version 3.9 or higher)
- [pip](https://pip.pypa.io/en/stable/installation/) (Python package installer)
- [Git](https://git-scm.com/downloads/) (for cloning the repository)
- An account with [Supabase](https://supabase.com/) for database and authentication services.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repo.git
    cd your-repo
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

The application uses environment variables for configuration. These variables are loaded from a `.env` file.

1.  **Create a `.env` file:**
    Copy the example environment file to create your own local configuration:
    ```bash
    cp .env.example .env
    ```

2.  **Update the environment variables:**
    Open the `.env` file in your editor and replace the placeholder values with your actual configuration. The most critical variables to set up are:
    - `SUPABASE_URL`: Your Supabase project URL.
    - `SUPABASE_ANON_KEY`: Your Supabase project's anonymous key.
    - `SUPABASE_SERVICE_KEY`: Your Supabase project's service role key.
    - `DATABASE_URL`: The connection string for your Supabase PostgreSQL database.
    - `JWT_SECRET`: A strong, secret key for signing JWTs.
    - `HUGGINGFACE_TOKEN`: Your Hugging Face access token for downloading the Surya-1.0 model.
    - `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`: If you intend to test payment processing.

## ▶️ Usage

### Running the Application

To start the development server, run the following command from the root of the project directory:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

### Running Tests

This project uses `pytest` for testing. To run the full test suite, use the following command:

```bash
pytest
```

Ensure you have a separate test database or have configured your environment appropriately to run tests without affecting your development data.

## 📚 API Documentation

The API is self-documenting, thanks to FastAPI. Once the application is running, you can access the interactive API documentation at the following URLs:

- **Swagger UI:** [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **ReDoc:** [`http://localhost:8000/redoc`](http://localhost:8000/redoc)

For more detailed information about the API, database schema, and other technical aspects, please refer to the `DEVELOPERS.md` file.

## 🤝 Contributing

Contributions are welcome! We have a set of guidelines to help you get started. Please refer to the `CONTRIBUTING.md` file for more information.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.