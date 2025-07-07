# ChatPLG-UI

A production-ready React chat application with live streaming responses from LLM models via vLLM server. Features Hebrew language support and real-time conversation management.

## Features

- 🎯 **Live Streaming**: Real-time streaming responses from LLM models
- 🌍 **Hebrew Support**: Full RTL support and Hebrew language interface
- 💬 **Multiple Conversations**: Manage multiple chat sessions with persistent storage
- 🔄 **Production Ready**: Built with FastAPI backend and React frontend
- 📱 **Responsive Design**: Mobile-friendly interface
- 🚀 **Easy Setup**: One-command startup script
- 🛠️ **Error Handling**: Comprehensive error handling and retry logic
- 👥 **Multi-user Support**: Supports multiple concurrent users

## Architecture

- **Frontend**: Next.js (React) with TypeScript
- **Backend**: FastAPI with streaming support
- **LLM Engine**: vLLM server for model inference
- **Storage**: Local storage for conversation persistence

## Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- npm or yarn
- A running vLLM server (see setup instructions below)

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ChatPLG-UI
   ```

2. **Start your vLLM server** (in a separate terminal):
   ```bash
   python -m vllm.entrypoints.openai.api_server \
     --model gaunernst/gemma-3-12b-it-qat-autoawq \
     --port 8000
   ```

3. **Run the application**:
   ```bash
   ./start.sh
   ```

The startup script will:
- Install Python and Node.js dependencies
- Start the FastAPI backend server on port 8090
- Start the React frontend on port 3000
- Automatically open the application in your browser

## Manual Setup

If you prefer to set up manually:

### Backend Setup

1. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the FastAPI server**:
   ```bash
   python server.py
   ```

### Frontend Setup

1. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

2. **Start the React development server**:
   ```bash
   npm run dev
   ```

## Usage

1. **Access the application**: Open http://localhost:3000 in your browser
2. **Start chatting**: Type your message in Hebrew or English
3. **Create new conversations**: Use the sidebar to manage multiple chat sessions
4. **Monitor API health**: Check http://localhost:8090/api/health for backend status

## API Endpoints

- `POST /api/chat/stream` - Stream chat completions
- `GET /api/health` - Health check with vLLM status
- `GET /api/metrics` - System metrics and active sessions

## Configuration

### Environment Variables

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8090)

### Backend Configuration

Edit `server.py` to modify:
- `VLLM_API_URL`: vLLM server URL
- `MODEL_NAME`: Model name for vLLM
- `SYSTEM_PROMPT`: System prompt for the assistant

## Development

### Project Structure

```
ChatPLG-UI/
├── src/
│   ├── app/                    # Next.js app router
│   ├── components/             # React components
│   ├── types/                  # TypeScript types
│   └── utils/                  # Utility functions
├── server.py                   # FastAPI backend
├── requirements.txt            # Python dependencies
├── start.sh                    # Startup script
└── README.md
```

### Key Components

- **ChatContainerComponent**: Main chat interface
- **StreamingAPI**: WebSocket-like streaming utilities
- **MessageComponent**: Individual message rendering
- **SidebarComponent**: Conversation management

## Production Deployment

For production deployment:

1. **Build the React app**:
   ```bash
   npm run build
   ```

2. **Start the production server**:
   ```bash
   npm start
   ```

3. **Configure reverse proxy** (nginx/Apache) to serve both frontend and API

## Troubleshooting

### Common Issues

1. **vLLM server not running**: Ensure your vLLM server is running on port 8000
2. **Port conflicts**: Check if ports 3000 and 8090 are available
3. **Memory issues**: Ensure sufficient RAM for both vLLM and the application
4. **Network errors**: Check firewall settings and network connectivity

### Logs

- Backend logs: Check the terminal running `python server.py`
- Frontend logs: Check browser console and terminal running `npm run dev`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Check the troubleshooting section above
- Review the logs for error messages
- Ensure all prerequisites are properly installed
