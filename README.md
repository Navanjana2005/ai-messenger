# AI Messenger

A voice-enabled messaging system powered by Mistral AI. This project provides real-time communication with AI capabilities using speech-to-text and text-to-speech features.

## Features

- **Voice Input/Output**: Speak to the AI and hear responses using text-to-speech
- **AI-Powered Chat**: Powered by Mistral AI for intelligent conversations
- **User Authentication**: Register and login with secure sessions
- **Client-Server Architecture**: Separate sender and receiver clients with a Flask backend
- **Database Integration**: SQLite for user management and activity logging
- **Logging System**: Comprehensive logging for debugging and monitoring

## Project Structure

```
├── main.py                 # Main entry point
├── server.py              # Flask server with authentication endpoints
├── sender_client.py       # Client for sending messages to the AI
├── receiver_client.py     # Client for receiving AI responses
├── speech_to_text.py      # Speech recognition module
├── text_to_speech.py      # Text-to-speech module
├── database.py            # Database operations
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Installation

### Prerequisites
- Python 3.8+
- Mistral API Key (sign up at [mistral.ai](https://mistral.ai))

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-messenger.git
cd ai-messenger
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your API key:
   - Set the `MISTRAL_API_KEY` environment variable, or
   - Update the `config.py` file with your Mistral API key

## Usage

### Start the Server
```bash
python server.py
```

### Run the Sender Client (Send Messages)
```bash
python sender_client.py
```

### Run the Receiver Client (Receive Messages)
```bash
python receiver_client.py
```

### Run Main Application
```bash
python main.py
```

## Configuration

Edit `config.py` to customize:
- Mistral API settings
- Database location
- Password salt length
- Session timeout
- Logging configuration

## API Endpoints

The Flask server provides the following endpoints:

- `POST /signup` - Register a new user
- `POST /login` - Authenticate user and get session token
- `POST /message` - Send a message
- `GET /messages/<user_id>` - Retrieve user messages
- Additional endpoints for activity logging and session verification

## Logging

All activities are logged to the `logs/` directory with timestamps. Logs include:
- Authentication events
- Message operations
- Errors and warnings
- System activity

## Requirements

See `requirements.txt` for all dependencies:
- flask - Web framework
- requests - HTTP client
- mistralai - Mistral AI API client
- pyttsx3 - Text-to-speech
- SpeechRecognition - Speech-to-text

## Security Notes

- Store API keys in environment variables, never commit them to git
- Use strong passwords for user accounts
- Session tokens expire after 1 hour (configurable)
- All passwords are hashed before storage

## License

[Add your license here]

## Contributing

Feel free to fork this project and submit pull requests.

## Support

For issues and questions, please open an issue on GitHub.
