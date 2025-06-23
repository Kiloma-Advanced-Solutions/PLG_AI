# ChatPLG - Hebrew RTL Chatbot

A modern Hebrew RTL (Right-to-Left) chatbot application built with React, Next.js, and TypeScript. This application is specifically designed for Hebrew text and includes a beautiful, responsive UI with dark/light theme support.

## Features

### 🎯 Core Features
- **Hebrew RTL Support**: Fully optimized for Hebrew text with proper RTL layout
- **Real-time Chat**: Interactive chat interface with message history
- **Conversation Management**: Create, switch between, and manage multiple conversations
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

### 🎨 UI Components
- **Header**: App name "ChatPLG" with logo and theme toggle
- **Sidebar**: Previous conversations list with hover functionality
- **Chat Interface**: Main conversation area with user and assistant messages
- **Theme Toggle**: Switch between light and dark modes
- **Message Components**: Beautiful message bubbles with timestamps

### 🔧 Technical Features
- **TypeScript**: Full type safety throughout the application
- **CSS Modules**: Scoped styling for each component
- **Local Storage**: Persistent conversation history
- **Responsive Design**: Mobile-first approach
- **Accessibility**: ARIA labels and keyboard navigation support

## Project Structure

```
src/
├── app/
│   ├── globals.css          # Global styles and RTL support
│   ├── layout.tsx           # Root layout with Hebrew metadata
│   └── page.tsx             # Main application page
├── components/
│   ├── chat-component/      # Main chat interface
│   ├── header-component/    # App header with logo and theme toggle
│   ├── message-component/   # Individual message display
│   ├── sidebar-component/   # Conversations sidebar
│   └── theme-toggle-component/ # Dark/light mode toggle
```

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd chatui
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

### Starting a New Chat
- Click the "צור שיחה חדשה" (Create New Chat) button in the sidebar
- Or simply start typing in the message input

### Managing Conversations
- Hover over the right edge to open the sidebar
- Click on any previous conversation to switch to it
- Conversations are automatically saved to localStorage

### Theme Switching
- Click the sun/moon icon in the header to toggle between light and dark modes
- Theme preference is saved and persists across sessions

### Sending Messages
- Type your message in Hebrew (or any language)
- Press Enter to send
- Use Shift+Enter for new lines

## Component Architecture

Each component follows a consistent structure:
- `component-name.tsx` - React component with TypeScript
- `component-name.module.css` - Scoped CSS styles
- Proper TypeScript interfaces for props
- RTL support and responsive design

### Key Components

#### HeaderComponent
- Displays app logo and name "ChatPLG"
- Includes theme toggle functionality
- Responsive design with proper RTL layout

#### SidebarComponent
- Shows previous conversations
- Hover-to-open functionality
- "Create New Chat" button
- Active conversation highlighting

#### ChatComponent
- Main conversation interface
- Message input with send button
- Loading states and typing indicators
- Auto-scroll to latest messages

#### MessageComponent
- Individual message display
- Different styles for user vs assistant
- Timestamp display
- RTL text alignment

## Styling

The application uses CSS Modules for component-scoped styling with:
- CSS custom properties for theming
- RTL-specific styles
- Dark mode support
- Responsive breakpoints
- Smooth animations and transitions

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Future Enhancements

- [ ] Real AI integration (OpenAI, Claude, etc.)
- [ ] Voice input/output support
- [ ] File upload capabilities
- [ ] Export conversation history
- [ ] User authentication
- [ ] Multi-language support
- [ ] Advanced conversation search
- [ ] Conversation sharing

---

Built with ❤️ for Hebrew speakers worldwide
