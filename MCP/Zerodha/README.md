# Zerodha Kite API Interaction Server (via MCP)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Optional: Choose your license -->

This project provides a server built using the **MCP (Multi-Context Platform)** framework (`FastMCP`) that exposes tools for interacting with the Zerodha Kite Connect API. It handles the complex OAuth2 authentication flow required by Zerodha, including running a local FastAPI server to capture the redirect, and securely manages API sessions.

Once running, you can interact with this server using an MCP client to perform various trading and portfolio management actions on your Zerodha account.

## Features

*   **Zerodha Authentication:** Handles the complete Kite Connect login flow using a browser redirect and a local callback server.
*   **Session Management:** Automatically generates and stores access tokens (`.tokens` file) for reuse across server restarts. Verifies token validity on startup.
*   **MCP Tool Integration:** Exposes various Kite Connect API functions as MCP tools, ready to be called by an MCP client.
*   **Equity Operations:**
    *   Get Holdings
    *   Get Positions
    *   Get Margins
    *   Place Orders (Regular, various types)
    *   Get Quotes
    *   Get Historical Data
*   **Mutual Fund Operations:**
    *   Get MF Orders
    *   Place MF Orders
    *   Cancel MF Orders
    *   Get MF Instruments list
    *   Get MF Holdings
    *   Get MF SIPs
    *   Place MF SIPs
    *   Modify MF SIPs
    *   Cancel MF SIPs
*   **Environment Variable Support:** Uses `.env` file for securely managing API keys.
*   **Asynchronous Design:** Leverages `asyncio`, `FastAPI`, and `httpx` for efficient operation.

## Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)
*   `git` (for cloning the repository)
*   Zerodha Kite Account
*   Zerodha Kite Connect API Key and API Secret (obtained from [Kite Developer Console](https://developers.kite.trade/))

## Setup & Installation

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-directory>
    ```

2.  **Create and Activate a Virtual Environment:**
    ```bash
    # Linux/macOS
    python3 -m venv venv
    source venv/bin/activate

    # Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *   **Note:** Ensure your `requirements.txt` file includes all necessary packages: `fastapi`, `uvicorn`, `python-dotenv`, `httpx`, `kiteconnect`, and **the specific MCP package you are using** (e.g., `mcp-server`, `fastmcp` - check its PyPI name).

4.  **Configure API Credentials:**
    *   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file and replace the placeholder values with your actual Zerodha Kite API Key and Secret:
        ```dotenv
        KITE_API_KEY=YOUR_ZERODHA_API_KEY_HERE
        KITE_API_SECRET=YOUR_ZERODHA_API_SECRET_HERE
        ```

5.  **Configure Kite Connect App:**
    *   Log in to your [Kite Developer Console](https://developers.kite.trade/).
    *   Go to your app settings.
    *   Ensure the **Redirect URL** is set *exactly* to: `http://127.0.0.1:5000/zerodha/auth/redirect`
    *   This *must* match the `REDIRECT_URL` used in the script for the login flow to work.

## Running the Server

Once the setup is complete, you can start the MCP server:

```bash
python your_script_name.py
