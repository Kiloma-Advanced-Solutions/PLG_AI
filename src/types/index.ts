export type Message = {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
};

export type Conversation = {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: string;
  messages: Message[];
}; 