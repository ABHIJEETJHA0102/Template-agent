# Real Estate Poster Template Agent API

A FastAPI-based agent system that can chat with users and generate customized real estate poster templates using the Templated.io API.

## Features

- RESTful API for real estate poster creation
- Session-based conversations
- Customizable poster elements (text, colors, images)
- Integration with Templated.io for professional poster generation
- LangGraph workflow for structured conversation and template generation

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Templated.io API key and template ID

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   ```
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - Unix/MacOS: `source .venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the root directory with the following content:

```
OPENAI_API_KEY=your_openai_api_key_here
TEMPLATED_API_KEY=your_templated_api_key_here
TEMPLATED_TEMPLATE_ID=your_template_id_here
```

## Usage

### Running the API Server

Start the FastAPI server:

```
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`.

### API Endpoints

#### Chat Endpoint

```
POST /chat
```

Request body:
```json
{
  "session_id": "optional-session-id",
  "user_prompt": "Your message here"
}
```

Response:
```json
{
  "session_id": "session-uuid",
  "response": "Agent's response",
  "status": "COLLECTING_INFO"
}
```

#### Session Status

```
GET /session/{session_id}
```

Response:
```json
{
  "status": "TEMPLATE_GENERATED",
  "has_template": true,
  "template_url": "https://templated-assets.s3.amazonaws.com/renders/example.jpg"
}
```

#### Delete Session

```
DELETE /session/{session_id}
```

Response:
```json
{
  "message": "Session deleted successfully"
}
```

### Example API Usage

1. Start a conversation:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_prompt": "I want to create a poster for my luxury apartment with an image at https://example.com/luxury-apt.jpg. The price is $2,500,000."}'
```

2. Continue the conversation using the returned session ID:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "returned-session-id", "user_prompt": "Change the modern text to LUXURY and make it gold colored."}'
```

3. Generate the poster:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "returned-session-id", "user_prompt": "Generate it please."}'
```

## Project Structure

- `app.py`: FastAPI application entry point
- `main.py`: Original CLI application (legacy)
- `agents/`: Contains the LangGraph agent implementation
  - `__init__.py`: Defines the agent graph structure
  - `nodes.py`: Implements the agent behavior and logic
  - `state.py`: Defines the agent state structure
  - `tools.py`: Implements the template generation tool
- `utils/`: Contains utility functions
  - `template_renderer.py`: Handles API communication with Templated.io

## License

MIT