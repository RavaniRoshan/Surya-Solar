# 🚀 Getting Started

This guide will walk you through setting up the ZERO-COMP Solar Weather API on your local machine for development and testing.

## Prerequisites

Before you begin, ensure you have the following installed:
- [Python](https://www.python.org/downloads/) (version 3.9 or higher)
- [pip](https://pip.pypa.io/en/stable/installation/) (Python package installer)
- [Git](https://git-scm.com/downloads/) (for cloning the repository)
- An account with [Supabase](https://supabase.com/) for database and authentication services.

## Installation

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

## Configuration

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
