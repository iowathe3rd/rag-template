# RAG API

## Overview

This project implements a Retrieval-Augmented Generation (RAG) API using FastAPI, Langchain, and other related libraries. It allows you to ingest documents, store them in a vector database, and then query them using natural language. The API also supports conversation history management.

## Features

- **Document Ingestion:** Supports various document types (PDF, TXT, Web) for indexing.
-**Vector Storage:** Uses ChromaDB for storing document embeddings.
-**RAG Pipeline:** Implements a RAG pipeline using Langchain for question answering.
-**Conversation History:** Manages conversation history for contextual question answering.
-**Asynchronous Operations:** Utilizes asyncio for efficient and concurrent processing.
-**API Endpoints:** Provides RESTful API endpoints for document ingestion and question answering.

## Setup

### Prerequisites

- Python 3.12 or higher
- Poetry for dependency management
- PostgreSQL database

### Installation

1.Clone the repository:

    ```bash
    git clone <your_repository_url>
    cd <your_project_directory>
    ```

2.Install dependencies using Poetry:

    ```bash
    poetry install
    ```

3.Set up environment variables:

    Create a `.env` file in the root directory and add the following variables:

    ```env
    POSTGRES_USER=<your_postgres_user>
    POSTGRES_PASSWORD=<your_postgres_password>
    POSTGRES_HOST=<your_postgres_host>
    POSTGRES_PORT=<your_postgres_port>
    POSTGRES_DB=<your_postgres_db>
    TOGETHERAI_API_KEY=<your_togetherai_api_key>
    LANGSMITH_API_KEY=<your_langsmith_api_key>
    ```

    Replace the placeholders with your actual values.

### Running the Application

To run the application, use the following command:

This will start the FastAPI application with hot reloading enabled.

## Usage

### API Endpoints

- **Ingest Document:**

    `POST /agents/{agent_id}/ingest`

- Upload a document for indexing.
- Supported file types: PDF, TXT.
- Request body: `multipart/form-data` with `file` and `source_type` fields.

- **Ask Question:**

    `POST /agents/{agent_id}/chats/{chat_id}/ask`

- Ask a question within a specific chat context.
- Request body: `{"question": "your question"}`

### Example

1.**Ingest a document:**

    ```bash
    curl -X POST \
      -H "Content-Type: multipart/form-data" \
      -F "file=@/path/to/your/document.pdf" \
      -F "source_type=pdf" \
      http://localhost:8000/agents/your_agent_id/ingest
    ```

2.  **Ask a question:**

    ```bash
    curl -X POST \
      -H "Content-Type: application/json" \
      -d '{"question": "What is the main topic?"}' \
      http://localhost:8000/agents/your_agent_id/chats/your_chat_id/ask
    ```

## Contributing

Feel free to contribute to the project by submitting pull requests or opening issues.

## License

This project is licensed under the MIT License.
