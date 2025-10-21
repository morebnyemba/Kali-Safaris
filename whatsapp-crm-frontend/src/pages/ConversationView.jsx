// src/pages/ConversationView.jsx

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { FiArrowLeft, FiSend, FiPaperclip, FiCheck, FiCheckCircle, FiClock, FiAlertTriangle } from 'react-icons/fi';
import { useAuth } from '@/context/AuthContext';
import { API_BASE_URL } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { toast } from 'sonner';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';

async function apiCall(endpoint, method = 'GET', body = null) {
  const token = localStorage.getItem('accessToken');
  const headers = {
    ...(!body || !(body instanceof FormData) && { 'Content-Type': 'application/json' }),
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
  const config = { method, headers, ...(body && !(body instanceof FormData) && { body: JSON.stringify(body) }) };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: `Request failed with status ${response.status}` }));
    throw new Error(errorData.detail || 'API request failed');
  }
  if (response.status === 204) return null;
  return response.json();
}

const MessageStatusIcon = ({ status }) => {
  switch (status) {
    case 'sent':
      return <FiCheck className="h-4 w-4 text-gray-400" title="Sent" />;
    case 'delivered':
      return <FiCheckCircle className="h-4 w-4 text-gray-400" title="Delivered" />;
    case 'read':
      return <FiCheckCircle className="h-4 w-4 text-blue-500" title="Read" />;
    case 'pending_dispatch':
    case 'dispatched':
      return <FiClock className="h-4 w-4 text-gray-400" title="Pending" />;
    case 'failed':
      return <FiAlertTriangle className="h-4 w-4 text-red-500" title="Failed" />;
    default:
      return null;
  }
};

export default function ConversationView() {
  const { contactId } = useParams();
  const { accessToken } = useAuth();
  const [contact, setContact] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const messagesEndRef = useRef(null);

  const getSocketUrl = useCallback(() => {
    if (accessToken && contactId) {
      return `${API_BASE_URL.replace(/^http/, 'ws')}/ws/conversations/${contactId}/?token=${accessToken}`;
    }
    return null;
  }, [accessToken, contactId]);

  const { sendJsonMessage, lastJsonMessage, readyState } = useWebSocket(getSocketUrl, {
    shouldReconnect: (closeEvent) => true,
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (lastJsonMessage) {
      console.log("Received message:", lastJsonMessage);
      setMessages(prevMessages => {
        const existingMessageIndex = prevMessages.findIndex(msg => msg.id === lastJsonMessage.id);
        if (existingMessageIndex !== -1) {
          const updatedMessages = [...prevMessages];
          updatedMessages[existingMessageIndex] = lastJsonMessage;
          return updatedMessages;
        } else {
          return [...prevMessages, lastJsonMessage];
        }
      });
    }
  }, [lastJsonMessage]);

  useEffect(() => {
    const fetchInitialData = async () => {
      setIsLoading(true);
      try {
        // These API endpoints need to be created in your `conversations` app
        const contactData = await apiCall(`/crm-api/conversations/contacts/${contactId}/`);
        const messagesData = await apiCall(`/crm-api/conversations/contacts/${contactId}/messages/`);
        setContact(contactData);
        setMessages(messagesData.results || []);
      } catch (error) {
        toast.error('Failed to load conversation data.');
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    if (contactId) {
      fetchInitialData();
    }
  }, [contactId]);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (newMessage.trim() && readyState === ReadyState.OPEN) {
      sendJsonMessage({
        message: newMessage.trim(),
      });
      setNewMessage('');
    } else if (readyState !== ReadyState.OPEN) {
      toast.warning("Connection is not open. Please wait.");
    }
  };

  const connectionStatus = {
    [ReadyState.CONNECTING]: { text: 'Connecting...', color: 'bg-yellow-500' },
    [ReadyState.OPEN]: { text: 'Connected', color: 'bg-green-500' },
    [ReadyState.CLOSING]: { text: 'Closing...', color: 'bg-orange-500' },
    [ReadyState.CLOSED]: { text: 'Disconnected', color: 'bg-red-500' },
    [ReadyState.UNINSTANTIATED]: { text: 'Instantiating...', color: 'bg-gray-500' },
  }[readyState];

  if (isLoading) {
    return (
      <div className="p-4">
        <Skeleton className="h-12 w-1/2 mb-4" />
        <div className="space-y-4">
          <Skeleton className="h-16 w-3/4" />
          <Skeleton className="h-16 w-3/4 ml-auto" />
          <Skeleton className="h-16 w-2/3" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-theme(space.24))] bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="flex items-center p-4 border-b bg-white dark:bg-gray-800 dark:border-gray-700 shadow-sm">
        <Link to="/conversation" className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700">
          <FiArrowLeft className="h-6 w-6" />
        </Link>
        <div className="flex items-center ml-4">
          <Avatar>
            <AvatarImage src={contact?.avatar_url} />
            <AvatarFallback>{contact?.name?.charAt(0) || 'C'}</AvatarFallback>
          </Avatar>
          <div className="ml-3">
            <h2 className="font-semibold text-lg">{contact?.name || 'Unknown Contact'}</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">{contact?.whatsapp_id}</p>
          </div>
        </div>
        <div className="ml-auto flex items-center space-x-2">
            <Badge variant="outline" className="flex items-center">
                <span className={`h-2 w-2 rounded-full mr-2 ${connectionStatus.color}`}></span>
                {connectionStatus.text}
            </Badge>
        </div>
      </header>

      {/* Messages Area */}
      <main className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.direction === 'out' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-xs md:max-w-md lg:max-w-2xl px-4 py-2 rounded-lg ${
              msg.direction === 'out'
                ? 'bg-blue-500 text-white rounded-br-none'
                : 'bg-white dark:bg-gray-700 dark:text-gray-200 rounded-bl-none shadow-sm'
            }`}>
              <p className="text-sm whitespace-pre-wrap">{msg.content_payload?.body || '[No Content]'}</p>
              <div className="flex items-center justify-end mt-1">
                <span className={`text-xs ${msg.direction === 'out' ? 'text-blue-200' : 'text-gray-400 dark:text-gray-500'}`}>
                  {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                {msg.direction === 'out' && (
                  <span className="ml-2">
                    <MessageStatusIcon status={msg.status} />
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </main>

      {/* Input Area */}
      <footer className="p-4 bg-white dark:bg-gray-800 border-t dark:border-gray-700">
        <form onSubmit={handleSendMessage} className="flex items-center space-x-4">
          <Button type="button" variant="ghost" size="icon">
            <FiPaperclip className="h-5 w-5" />
          </Button>
          <Input
            type="text"
            placeholder="Type a message..."
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            className="flex-1"
            disabled={readyState !== ReadyState.OPEN}
          />
          <Button type="submit" size="icon" disabled={readyState !== ReadyState.OPEN}>
            <FiSend className="h-5 w-5" />
          </Button>
        </form>
      </footer>
    </div>
  );
}