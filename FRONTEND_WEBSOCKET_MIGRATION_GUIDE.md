# Frontend WebSocket Migration Guide: Socket.io to Native WebSockets

## Overview
Migrate your React Native frontend from Socket.io to native WebSockets to connect with your Django Channels backend.

## Step 1: Remove Socket.io Dependencies

```bash
# Remove Socket.io packages
npm uninstall socket.io-client
# or
yarn remove socket.io-client
```

## Step 2: Create WebSocket Service

Create a new file: `services/WebSocketService.js`

```javascript
class WebSocketService {
  constructor() {
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 3000;
    this.eventListeners = new Map();
    this.isConnecting = false;
    this.shouldReconnect = true;
  }

  // Connect to WebSocket
  connect(url, token) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return Promise.resolve();
    }

    if (this.isConnecting) {
      console.log('WebSocket connection already in progress');
      return Promise.resolve();
    }

    this.isConnecting = true;
    this.shouldReconnect = true;
    
    // Add token to URL
    const wsUrl = `${url}?token=${token}`;
    
    return new Promise((resolve, reject) => {
      try {
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = (event) => {
          console.log('WebSocket connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.emit('connect', event);
          resolve();
        };

        this.socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', data);
            
            // Emit event based on message type
            if (data.type) {
              this.emit(data.type, data);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.socket.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          this.isConnecting = false;
          this.emit('disconnect', event);
          
          if (this.shouldReconnect) {
            this.handleReconnect();
          }
        };

        this.socket.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          this.emit('error', error);
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  // Send message to WebSocket
  send(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      this.socket.send(message);
      return true;
    } else {
      console.warn('WebSocket not connected, cannot send message');
      return false;
    }
  }

  // Disconnect WebSocket
  disconnect() {
    this.shouldReconnect = false;
    if (this.socket) {
      this.socket.close(1000, 'Client disconnecting');
      this.socket = null;
    }
  }

  // Handle reconnection
  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        if (this.shouldReconnect) {
          // You'll need to store the URL and token for reconnection
          // This will be handled in the chat service
          this.emit('reconnect_attempt', this.reconnectAttempts);
        }
      }, this.reconnectInterval);
    } else {
      console.log('Max reconnection attempts reached');
      this.emit('reconnect_failed');
    }
  }

  // Event listener management
  on(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  // Get connection status
  isConnected() {
    return this.socket && this.socket.readyState === WebSocket.OPEN;
  }

  // Get connection state
  getReadyState() {
    if (!this.socket) return WebSocket.CLOSED;
    return this.socket.readyState;
  }
}

export default new WebSocketService();
```

## Step 3: Create Chat Service

Create a new file: `services/ChatService.js`

```javascript
import WebSocketService from './WebSocketService';
import AsyncStorage from '@react-native-async-storage/async-storage';

class ChatService {
  constructor() {
    this.currentRoomId = null;
    this.presenceSocket = null;
    this.chatSocket = null;
    this.baseUrl = process.env.EXPO_PUBLIC_WEBSOCKET_URL || 'wss://vauice-backend.onrender.com';
  }

  // Initialize chat connection
  async connectToChat(roomId) {
    try {
      const token = await this.getAuthToken();
      if (!token) {
        throw new Error('No authentication token found');
      }

      this.currentRoomId = roomId;
      const chatUrl = `${this.baseUrl}/ws/chat/${roomId}/`;
      
      // Create new WebSocket instance for chat
      this.chatSocket = new WebSocketService();
      
      // Set up event listeners before connecting
      this.setupChatEventListeners();
      
      // Connect to chat room
      await this.chatSocket.connect(chatUrl, token);
      
      return true;
    } catch (error) {
      console.error('Error connecting to chat:', error);
      throw error;
    }
  }

  // Initialize presence connection
  async connectToPresence() {
    try {
      const token = await this.getAuthToken();
      if (!token) {
        throw new Error('No authentication token found');
      }

      const presenceUrl = `${this.baseUrl}/ws/presence/`;
      
      // Create new WebSocket instance for presence
      this.presenceSocket = new WebSocketService();
      
      // Set up event listeners before connecting
      this.setupPresenceEventListeners();
      
      // Connect to presence
      await this.presenceSocket.connect(presenceUrl, token);
      
      // Start heartbeat
      this.startHeartbeat();
      
      return true;
    } catch (error) {
      console.error('Error connecting to presence:', error);
      throw error;
    }
  }

  // Setup chat event listeners
  setupChatEventListeners() {
    // Connection events
    this.chatSocket.on('connect', () => {
      console.log('Connected to chat room:', this.currentRoomId);
      this.onChatConnected();
    });

    this.chatSocket.on('disconnect', () => {
      console.log('Disconnected from chat room');
      this.onChatDisconnected();
    });

    // Chat message events
    this.chatSocket.on('chat_message', (data) => {
      this.onMessageReceived(data);
    });

    this.chatSocket.on('message_edited', (data) => {
      this.onMessageEdited(data);
    });

    this.chatSocket.on('message_deleted', (data) => {
      this.onMessageDeleted(data);
    });

    // User presence events
    this.chatSocket.on('user_joined', (data) => {
      this.onUserJoined(data);
    });

    this.chatSocket.on('user_left', (data) => {
      this.onUserLeft(data);
    });

    // Typing indicator events
    this.chatSocket.on('typing_indicator', (data) => {
      this.onTypingIndicator(data);
    });

    // Error handling
    this.chatSocket.on('error', (error) => {
      console.error('Chat WebSocket error:', error);
      this.onChatError(error);
    });

    // Reconnection events
    this.chatSocket.on('reconnect_attempt', (attempt) => {
      console.log(`Chat reconnection attempt ${attempt}`);
    });

    this.chatSocket.on('reconnect_failed', () => {
      console.log('Chat reconnection failed');
      this.onChatReconnectFailed();
    });
  }

  // Setup presence event listeners
  setupPresenceEventListeners() {
    this.presenceSocket.on('connect', () => {
      console.log('Connected to presence service');
      this.onPresenceConnected();
    });

    this.presenceSocket.on('disconnect', () => {
      console.log('Disconnected from presence service');
      this.onPresenceDisconnected();
    });

    this.presenceSocket.on('notification', (data) => {
      this.onNotificationReceived(data);
    });

    this.presenceSocket.on('heartbeat_ack', (data) => {
      // Heartbeat acknowledged
      console.log('Heartbeat acknowledged');
    });
  }

  // Send chat message
  sendMessage(content, messageType = 'text', replyToId = null) {
    if (!this.chatSocket || !this.chatSocket.isConnected()) {
      throw new Error('Chat not connected');
    }

    const message = {
      type: 'chat_message',
      encrypted_content: content, // You may need to encrypt this
      content_hash: this.generateContentHash(content),
      message_type: messageType,
      reply_to: replyToId
    };

    return this.chatSocket.send(message);
  }

  // Send typing indicator
  startTyping() {
    if (this.chatSocket && this.chatSocket.isConnected()) {
      this.chatSocket.send({
        type: 'typing_start'
      });
    }
  }

  stopTyping() {
    if (this.chatSocket && this.chatSocket.isConnected()) {
      this.chatSocket.send({
        type: 'typing_stop'
      });
    }
  }

  // Mark message as read
  markMessageAsRead(messageId) {
    if (this.chatSocket && this.chatSocket.isConnected()) {
      this.chatSocket.send({
        type: 'message_read',
        message_id: messageId
      });
    }
  }

  // Edit message
  editMessage(messageId, newContent) {
    if (this.chatSocket && this.chatSocket.isConnected()) {
      this.chatSocket.send({
        type: 'message_edit',
        message_id: messageId,
        encrypted_content: newContent,
        content_hash: this.generateContentHash(newContent)
      });
    }
  }

  // Delete message
  deleteMessage(messageId) {
    if (this.chatSocket && this.chatSocket.isConnected()) {
      this.chatSocket.send({
        type: 'message_delete',
        message_id: messageId
      });
    }
  }

  // Start heartbeat for presence
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.presenceSocket && this.presenceSocket.isConnected()) {
        this.presenceSocket.send({
          type: 'heartbeat'
        });
      }
    }, 30000); // Send heartbeat every 30 seconds
  }

  // Stop heartbeat
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  // Disconnect from chat
  disconnectFromChat() {
    if (this.chatSocket) {
      this.chatSocket.disconnect();
      this.chatSocket = null;
    }
    this.currentRoomId = null;
  }

  // Disconnect from presence
  disconnectFromPresence() {
    this.stopHeartbeat();
    if (this.presenceSocket) {
      this.presenceSocket.disconnect();
      this.presenceSocket = null;
    }
  }

  // Disconnect all
  disconnectAll() {
    this.disconnectFromChat();
    this.disconnectFromPresence();
  }

  // Utility methods
  async getAuthToken() {
    try {
      const token = await AsyncStorage.getItem('access_token');
      return token?.replace('Bearer ', '');
    } catch (error) {
      console.error('Error getting auth token:', error);
      return null;
    }
  }

  generateContentHash(content) {
    // Simple hash function - you might want to use a proper crypto library
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return hash.toString();
  }

  // Event callbacks - override these in your components
  onChatConnected() {
    // Override in component
  }

  onChatDisconnected() {
    // Override in component
  }

  onPresenceConnected() {
    // Override in component
  }

  onPresenceDisconnected() {
    // Override in component
  }

  onMessageReceived(data) {
    // Override in component
  }

  onMessageEdited(data) {
    // Override in component
  }

  onMessageDeleted(data) {
    // Override in component
  }

  onUserJoined(data) {
    // Override in component
  }

  onUserLeft(data) {
    // Override in component
  }

  onTypingIndicator(data) {
    // Override in component
  }

  onNotificationReceived(data) {
    // Override in component
  }

  onChatError(error) {
    // Override in component
  }

  onChatReconnectFailed() {
    // Override in component
  }
}

export default new ChatService();
```

## Step 4: Update Your Chat Component

Replace your existing Socket.io usage:

```javascript
import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList } from 'react-native';
import ChatService from '../services/ChatService';

const ChatScreen = ({ route }) => {
  const { roomId } = route.params;
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [typingUsers, setTypingUsers] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    // Setup event callbacks
    ChatService.onChatConnected = () => {
      setIsConnected(true);
    };

    ChatService.onChatDisconnected = () => {
      setIsConnected(false);
    };

    ChatService.onMessageReceived = (data) => {
      const newMessage = {
        id: data.message_id,
        text: data.encrypted_content, // You may need to decrypt this
        senderId: data.sender_id,
        senderName: data.sender_username,
        timestamp: new Date(data.timestamp),
        type: data.message_type,
        isEdited: data.is_edited,
        replyTo: data.reply_to
      };
      
      setMessages(prev => [...prev, newMessage]);
    };

    ChatService.onMessageEdited = (data) => {
      setMessages(prev => 
        prev.map(msg => 
          msg.id === data.message.message_id 
            ? { ...msg, text: data.message.encrypted_content, isEdited: true }
            : msg
        )
      );
    };

    ChatService.onMessageDeleted = (data) => {
      setMessages(prev => 
        prev.filter(msg => msg.id !== data.message_id)
      );
    };

    ChatService.onTypingIndicator = (data) => {
      if (data.is_typing) {
        setTypingUsers(prev => 
          prev.includes(data.username) ? prev : [...prev, data.username]
        );
      } else {
        setTypingUsers(prev => 
          prev.filter(user => user !== data.username)
        );
      }
    };

    ChatService.onUserJoined = (data) => {
      console.log(`${data.username} joined the chat`);
    };

    ChatService.onUserLeft = (data) => {
      console.log(`${data.username} left the chat`);
    };

    // Connect to chat and presence
    const connect = async () => {
      try {
        await ChatService.connectToChat(roomId);
        await ChatService.connectToPresence();
      } catch (error) {
        console.error('Connection error:', error);
      }
    };

    connect();

    // Cleanup on unmount
    return () => {
      ChatService.disconnectAll();
    };
  }, [roomId]);

  // Handle typing
  const handleTyping = useCallback((text) => {
    setInputText(text);
    
    if (!isTyping && text.length > 0) {
      setIsTyping(true);
      ChatService.startTyping();
    } else if (isTyping && text.length === 0) {
      setIsTyping(false);
      ChatService.stopTyping();
    }
  }, [isTyping]);

  // Stop typing after delay
  useEffect(() => {
    if (isTyping) {
      const timeout = setTimeout(() => {
        setIsTyping(false);
        ChatService.stopTyping();
      }, 3000);
      
      return () => clearTimeout(timeout);
    }
  }, [isTyping, inputText]);

  // Send message
  const sendMessage = () => {
    if (inputText.trim() && isConnected) {
      try {
        ChatService.sendMessage(inputText.trim());
        setInputText('');
        if (isTyping) {
          setIsTyping(false);
          ChatService.stopTyping();
        }
      } catch (error) {
        console.error('Error sending message:', error);
      }
    }
  };

  // Render message item
  const renderMessage = ({ item }) => (
    <View style={{ padding: 10, marginVertical: 5 }}>
      <Text style={{ fontWeight: 'bold' }}>{item.senderName}</Text>
      <Text>{item.text}</Text>
      <Text style={{ fontSize: 12, color: 'gray' }}>
        {item.timestamp.toLocaleTimeString()}
        {item.isEdited && ' (edited)'}
      </Text>
    </View>
  );

  return (
    <View style={{ flex: 1 }}>
      {/* Connection status */}
      <View style={{ padding: 10, backgroundColor: isConnected ? 'green' : 'red' }}>
        <Text style={{ color: 'white', textAlign: 'center' }}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </Text>
      </View>

      {/* Messages list */}
      <FlatList
        data={messages}
        renderItem={renderMessage}
        keyExtractor={item => item.id}
        style={{ flex: 1 }}
      />

      {/* Typing indicator */}
      {typingUsers.length > 0 && (
        <View style={{ padding: 10 }}>
          <Text style={{ fontStyle: 'italic', color: 'gray' }}>
            {typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...
          </Text>
        </View>
      )}

      {/* Input area */}
      <View style={{ flexDirection: 'row', padding: 10 }}>
        <TextInput
          style={{ flex: 1, borderWidth: 1, padding: 10, marginRight: 10 }}
          value={inputText}
          onChangeText={handleTyping}
          placeholder="Type a message..."
          multiline
        />
        <TouchableOpacity
          onPress={sendMessage}
          disabled={!isConnected || !inputText.trim()}
          style={{ 
            padding: 10, 
            backgroundColor: isConnected && inputText.trim() ? 'blue' : 'gray'
          }}
        >
          <Text style={{ color: 'white' }}>Send</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

export default ChatScreen;
```

## Step 5: Update Environment Variables

Update your `.env` file:

```env
# Keep the same base URL
EXPO_PUBLIC_API_BASE_URL=https://vauice-backend.onrender.com/api/v1

# WebSocket URL (no Socket.io needed)
EXPO_PUBLIC_WEBSOCKET_URL=wss://vauice-backend.onrender.com

# Remove this if you had it
# EXPO_PUBLIC_ENABLE_WEBSOCKET=true
```

## Step 6: Handle Authentication

Update your authentication service to work with WebSocket query parameters:

```javascript
// In your auth service
export const getWebSocketToken = async () => {
  const token = await AsyncStorage.getItem('access_token');
  // Remove 'Bearer ' prefix if present
  return token?.replace('Bearer ', '');
};
```

## Step 7: Error Handling & Reconnection

Add robust error handling:

```javascript
// In your main App component or context
useEffect(() => {
  const handleAppStateChange = (nextAppState) => {
    if (nextAppState === 'active') {
      // Reconnect when app becomes active
      ChatService.connectToPresence();
    } else if (nextAppState === 'background') {
      // Optionally disconnect when app goes to background
      // ChatService.disconnectFromPresence();
    }
  };

  const subscription = AppState.addEventListener('change', handleAppStateChange);
  return () => subscription?.remove();
}, []);
```

## Key Differences from Socket.io:

1. **Connection**: Use `new WebSocket(url)` instead of `io(url)`
2. **Authentication**: Token in URL query string, not in auth object
3. **Events**: Manual event handling with `onmessage` instead of `socket.on()`
4. **Data Format**: All messages must be JSON strings
5. **Reconnection**: Manual implementation required
6. **Room Management**: URL-based room connections

## Backend WebSocket Endpoints:

Your Django backend provides these WebSocket endpoints:

1. **Chat Room**: `wss://vauice-backend.onrender.com/ws/chat/{roomId}/?token={jwtToken}`
2. **Presence**: `wss://vauice-backend.onrender.com/ws/presence/?token={jwtToken}`

## Message Types Supported by Backend:

### Outgoing (Frontend → Backend):
- `chat_message` - Send a new message
- `typing_start` - Start typing indicator
- `typing_stop` - Stop typing indicator
- `message_read` - Mark message as read
- `message_edit` - Edit existing message
- `message_delete` - Delete message
- `heartbeat` - Keep presence alive

### Incoming (Backend → Frontend):
- `chat_message` - New message received
- `message_edited` - Message was edited
- `message_deleted` - Message was deleted
- `user_joined` - User joined chat room
- `user_left` - User left chat room
- `typing_indicator` - Someone is typing
- `notification` - Push notification
- `heartbeat_ack` - Heartbeat response

## Testing:

1. **Test WebSocket connection**: Use `wscat` tool:
   ```bash
   wscat -c "wss://vauice-backend.onrender.com/ws/presence/?token=YOUR_TOKEN"
   ```

2. **Monitor network traffic** in React Native Debugger

3. **Check Django backend logs** for connection attempts

## Migration Checklist:

- [ ] Remove Socket.io dependencies
- [ ] Create WebSocketService.js
- [ ] Create ChatService.js
- [ ] Update chat components
- [ ] Update environment variables
- [ ] Update authentication handling
- [ ] Add error handling
- [ ] Test connections
- [ ] Test message sending/receiving
- [ ] Test typing indicators
- [ ] Test reconnection logic

Your Django Channels backend is properly configured and ready - this frontend migration will make everything work seamlessly!