// src/pages/ConversationsPage.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useAtom } from 'jotai';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from 'sonner';
import {
  FiSend, FiUsers, FiMessageSquare, FiSearch,
  FiLoader, FiAlertCircle, FiPaperclip, 
  FiArrowLeft, FiCheck, FiClock, FiMoreVertical, FiChevronRight,
  FiList, FiArrowRight, FiRadio, FiShield, FiZap
} from 'react-icons/fi';
import { formatDistanceToNow, parseISO } from 'date-fns';
import { contactsApi, API_BASE_URL } from '@/lib/api';
import { selectedContactAtom } from '@/atoms/conversationAtoms';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { useDebounce } from 'use-debounce';
import { useAuth } from '@/context/AuthContext';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { APP_ROLES, getRoleFromUser, hasPermission, hasRole } from '@/lib/rbac';
import { normalizeToken } from '@/services/auth';

const InteractiveReplyContent = ({ reply }) => {
  const { type, button_reply, list_reply } = reply;

  if (type === 'button_reply' && button_reply) {
    return (
      <div className="flex items-center gap-2 p-1 rounded-md bg-black/5 dark:bg-white/5">
        <FiArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
        <span className="font-medium text-sm">{button_reply.title}</span>
      </div>
    );
  }

  if (type === 'list_reply' && list_reply) {
    return (
      <div className="flex flex-col gap-1 p-2 rounded-md bg-black/5 dark:bg-white/5">
        <div className="flex items-center gap-2">
          <FiArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
          <span className="font-medium text-sm">{list_reply.title}</span>
        </div>
        {list_reply.description && (
          <span className="text-xs text-muted-foreground pl-6">{list_reply.description}</span>
        )}
      </div>
    );
  }

  return <span className="italic text-muted-foreground/80">[Interactive Reply: {type}]</span>;
};

const InteractiveMessageContent = ({ payload }) => {
  if (!payload || !payload.interactive) {
    return <span className="italic text-muted-foreground/80">[Unsupported interactive message]</span>;
  }

  const { type, header, body, footer, action } = payload.interactive;

  if (type === 'button' || type === 'list') {
    return (
      <div className="space-y-2">
        {header && <div className="font-bold">{header.type === 'text' ? header.text : `[${header.type} Header]`}</div>}
        {body && <p className="text-sm">{body.text}</p>}
        {footer && <p className="text-xs italic text-muted-foreground/80 pt-1">{footer.text}</p>}
        
        {type === 'button' && action?.buttons && (
          <div className="pt-2 space-y-1.5">
            {action.buttons.map(button => (
              <div key={button.reply.id} className="w-full text-center bg-background/20 dark:bg-background/50 rounded-md p-2 text-sm font-medium cursor-pointer hover:bg-background/40">
                {button.reply.title}
              </div>
            ))}
          </div>
        )}
        {type === 'list' && action?.sections && (
          <div className="pt-2"><div className="w-full text-left bg-background/20 dark:bg-background/50 rounded-md p-2 text-sm font-medium cursor-pointer hover:bg-background/40 flex items-center justify-between"><span><FiList className="inline mr-2" /> {action.button || 'View Options'}</span><FiChevronRight /></div></div>
        )}
      </div>
    );
  }

  if (type === 'button_reply' || type === 'list_reply') {
    return <InteractiveReplyContent reply={payload.interactive} />;
  }

  return <span className="italic text-muted-foreground/80">[Unsupported interactive type: {type}]</span>;
};

const MessageBubble = ({ message, contactName, isLast }) => {
  const isOutgoing = message.direction === 'out';
  const bubbleClass = isOutgoing 
    ? 'bg-primary text-primary-foreground rounded-se-none' 
    : 'bg-muted text-foreground rounded-ss-none';

  const statusIcons = {
    sent: <FiCheck className="h-3 w-3 text-muted-foreground" title="Sent" />,
    delivered: <div className="flex gap-0.5"><FiCheck className="h-3 w-3 text-muted-foreground" /><FiCheck className="h-3 w-3 text-muted-foreground -ml-1" /></div>,
    read: <div className="flex gap-0.5"><FiCheck className="h-3 w-3 text-blue-500" /><FiCheck className="h-3 w-3 text-blue-500 -ml-1" /></div>,
    failed: <FiAlertCircle className="h-3 w-3 text-destructive" />,
    pending: <FiClock className="h-3 w-3 text-muted-foreground animate-pulse" />
  };

  return (
    <div className={`flex flex-col my-1.5 ${isOutgoing ? 'items-end' : 'items-start'}`}>
      <div className={`max-w-[85%] px-3 py-2 rounded-xl shadow-sm ${bubbleClass}`} title={message.timestamp ? new Date(message.timestamp).toLocaleString() : ''}>
        <div className="text-sm wrap-break-word">
          {message.message_type === 'interactive' ? (
            <InteractiveMessageContent payload={message.content_payload} />
          ) : message.text_content ? (
            <p>{message.text_content}</p>
          ) : (
            <p className="italic text-muted-foreground/80">{message.content_preview || '[Unsupported message type]'}</p>
          )}
        </div>
      </div>
      <div className={`flex items-center gap-1 mt-1 px-1 ${isOutgoing ? 'flex-row-reverse' : ''}`}>
        <span className="text-xs text-muted-foreground">
          {message.timestamp ? formatDistanceToNow(parseISO(message.timestamp), { addSuffix: true }) : 'Sending...'}
        </span>
        {isOutgoing && message.status && (
          <span className={isLast ? 'opacity-100' : 'opacity-0'}>
            {statusIcons[message.status] || null}
          </span>
        )}
      </div>
    </div>
  );
};

const ContactListItem = React.memo(({ contact, isSelected, onSelect, hasUnread }) => {
  return (
    <div
      onClick={() => onSelect(contact)}
      className={`p-3 cursor-pointer transition-colors ${
        isSelected 
          ? 'bg-cyan-50 border-l-4 border-cyan-600 dark:bg-cyan-950/20' 
          : 'hover:bg-muted/50'
      }`}
    >
      <div className="flex items-center gap-3">
        <div className="relative">
          <Avatar className="h-10 w-10">
            <AvatarImage src={`https://ui-avatars.com/api/?name=${encodeURIComponent(contact.name || contact.whatsapp_id)}&background=random`} />
            <AvatarFallback>{contact.name?.substring(0,2) || 'CN'}</AvatarFallback>
          </Avatar>
          {hasUnread && (
            <div className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-primary border-2 border-background" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <p className="font-medium truncate">{contact.name || contact.whatsapp_id}</p>
              {contact.needs_human_intervention && <FiAlertCircle title="Needs Human Intervention" className="h-4 w-4 text-red-500 shrink-0"/>}
            </div>
            <div className="flex items-center gap-2">
              {hasUnread && <Badge className="bg-cyan-600 text-white hover:bg-cyan-600">New</Badge>}
              <FiChevronRight className="h-4 w-4 text-muted-foreground" />
            </div>
          </div>
          <p className="text-xs text-muted-foreground truncate">
            {contact.last_message_preview || 'No messages yet'}
          </p>
        </div>
      </div>
    </div>
  );
});

export default function ConversationsPage() {
  const [contacts, setContacts] = useState([]);
  const [selectedContact, setSelectedContact] = useAtom(selectedContactAtom);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [showNeedsAttentionOnly, setShowNeedsAttentionOnly] = useState(false);
  const [isLoading, setIsLoading] = useState({
    contacts: true,
    messages: false
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm] = useDebounce(searchTerm, 300);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const { accessToken, user } = useAuth();
  const wsToken = normalizeToken(accessToken);
  const isJwtToken = /^[-A-Za-z0-9_]+\.[-A-Za-z0-9_]+\.[-A-Za-z0-9_]+$/.test(wsToken);
  const userRole = getRoleFromUser(user);
  const canManageAutomation = hasRole(user, [APP_ROLES.ADMIN, APP_ROLES.MANAGER]);
  const canReply = hasPermission(user, ['conversations.add_message'])
    || hasRole(user, [APP_ROLES.ADMIN, APP_ROLES.MANAGER, APP_ROLES.AGENT]);

  // WebSocket Setup
  const getSocketUrl = useCallback(() => {
    if (isJwtToken && selectedContact?.id) {
      return `${API_BASE_URL.replace(/^http/, 'ws')}/ws/conversations/${selectedContact.id}/?token=${wsToken}`;
    }
    return null;
  }, [isJwtToken, selectedContact, wsToken]);

  const { sendJsonMessage, lastJsonMessage, readyState } = useWebSocket(getSocketUrl, {
    shouldReconnect: (closeEvent) => true,
  });
  
  const fetchContacts = useCallback(async (search = '') => {
    setIsLoading(prev => ({ ...prev, contacts: true }));
    try {
      const response = await contactsApi.list({ search });
      const data = response.data;
      setContacts(data.results || data || []);
    } catch (error) {
      toast.error("Couldn't load contacts");
    } finally {
      setIsLoading(prev => ({ ...prev, contacts: false }));
    }
  }, []);

  const fetchMessages = useCallback(async (contactId) => {
    if (!contactId) return;
    setIsLoading(prev => ({ ...prev, messages: true }));
    try {
      const response = await contactsApi.listMessages(contactId);
      const data = response.data;
      setMessages((data.results || data || []).reverse());
    } catch (error) {
      toast.error("Couldn't load messages");
    } finally {
      setIsLoading(prev => ({ ...prev, messages: false }));
    }
  }, []);

  useEffect(() => {
    fetchContacts(debouncedSearchTerm);
  }, [debouncedSearchTerm, fetchContacts]);

  useEffect(() => {
    if (selectedContact) {
      fetchMessages(selectedContact.id);
      inputRef.current?.focus();
    } else {
      setMessages([]);
    }
  }, [selectedContact, fetchMessages]);

  useEffect(() => {
    if (!lastJsonMessage) return;

    const { type, message, contact: updatedContactData } = lastJsonMessage;

    if (type === 'new_message' && message) {
      setMessages(prevMessages => {
        const existingMessageIndex = prevMessages.findIndex(msg => msg.id === message.id);
        if (existingMessageIndex !== -1) {
          const updatedMessages = [...prevMessages];
          updatedMessages[existingMessageIndex] = message;
          return updatedMessages;
        }
        return [...prevMessages, message];
      });
    } else if (type === 'contact_updated' && updatedContactData && selectedContact?.id === updatedContactData.id) {
      // Update the selected contact in the main panel
      setSelectedContact(updatedContactData);
      // Update the contact in the list on the left
      setContacts(prevContacts => 
        prevContacts.map(c => c.id === updatedContactData.id ? { ...c, ...updatedContactData } : c)
      );
    }
  }, [lastJsonMessage, selectedContact?.id, setContacts, setSelectedContact]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const filteredContacts = useMemo(() => {
    return contacts.filter((contact) => {
      if (showNeedsAttentionOnly && !contact.needs_human_intervention) {
        return false;
      }
      return true;
    });
  }, [contacts, showNeedsAttentionOnly]);

  const inboxStats = useMemo(() => ({
    total: contacts.length,
    live: contacts.filter((contact) => contact.unread_count > 0).length,
    attention: contacts.filter((contact) => contact.needs_human_intervention).length,
  }), [contacts]);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedContact) return;

    if (readyState === ReadyState.OPEN) {
      sendJsonMessage({ type: 'send_message', message: newMessage.trim() });
      setNewMessage('');
    } else {
      toast.error("Cannot send message. Connection is not live.");
    }
  };

  const handleToggleIntervention = () => {
    if (!selectedContact || readyState !== ReadyState.OPEN) {
      toast.error("Cannot update status. Connection is not live.");
      return;
    }
    if (!canManageAutomation) {
      toast.error('Only managers and administrators can change automation state.');
      return;
    }
    sendJsonMessage({ type: 'toggle_intervention' });
    // The UI will update reactively when the `contact_updated` message is received.
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  const connectionStatus = {
    [ReadyState.CONNECTING]: { text: 'Connecting...', color: 'text-yellow-500', bgColor: 'bg-yellow-500' },
    [ReadyState.OPEN]: { text: 'Live', color: 'text-green-500', bgColor: 'bg-green-500' },
    [ReadyState.CLOSING]: { text: 'Closing...', color: 'text-orange-500', bgColor: 'bg-orange-500' },
    [ReadyState.CLOSED]: { text: 'Disconnected', color: 'text-red-500', bgColor: 'bg-red-500' },
    [ReadyState.UNINSTANTIATED]: { text: 'Offline', color: 'text-gray-500', bgColor: 'bg-gray-500' },
  }[readyState];

  return (
    <div className="flex h-[calc(100vh-10rem)] flex-1 overflow-hidden rounded-[28px] border border-slate-200/80 bg-white/90 shadow-xl dark:border-slate-700 dark:bg-slate-900/90">
      {/* Conversations Panel */}
      <div className={`
        ${selectedContact ? 'hidden md:flex md:w-96' : 'flex w-full'} 
        border-r flex-col bg-slate-50/90 transition-all duration-300 h-full dark:bg-slate-950/60
      `}>
        <div className="border-b border-slate-200 p-5 dark:border-slate-800">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-600 dark:text-cyan-400">Realtime Workspace</p>
              <h1 className="mt-1 text-2xl font-semibold text-slate-900 dark:text-slate-100">Inbox</h1>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Live WhatsApp conversations with operator controls.</p>
            </div>
            <Badge variant="outline" className="border-cyan-200 text-cyan-700 dark:border-cyan-800 dark:text-cyan-300">
              {userRole}
            </Badge>
          </div>

          <div className="mt-4 grid grid-cols-3 gap-2">
            <div className="rounded-2xl bg-white p-3 shadow-sm dark:bg-slate-900">
              <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400"><FiUsers className="h-3.5 w-3.5" />Total</div>
              <div className="mt-1 text-xl font-semibold text-slate-900 dark:text-slate-100">{inboxStats.total}</div>
            </div>
            <div className="rounded-2xl bg-white p-3 shadow-sm dark:bg-slate-900">
              <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400"><FiRadio className="h-3.5 w-3.5" />Live</div>
              <div className="mt-1 text-xl font-semibold text-slate-900 dark:text-slate-100">{inboxStats.live}</div>
            </div>
            <div className="rounded-2xl bg-white p-3 shadow-sm dark:bg-slate-900">
              <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400"><FiShield className="h-3.5 w-3.5" />Attention</div>
              <div className="mt-1 text-xl font-semibold text-slate-900 dark:text-slate-100">{inboxStats.attention}</div>
            </div>
          </div>

          <div className="mt-4 flex items-center gap-2">
            <Button
              type="button"
              variant={showNeedsAttentionOnly ? 'default' : 'outline'}
              className={showNeedsAttentionOnly ? 'bg-cyan-600 text-white hover:bg-cyan-700' : ''}
              onClick={() => setShowNeedsAttentionOnly((current) => !current)}
            >
              <FiZap className="h-4 w-4" />
              Needs attention
            </Button>
            <Badge variant="secondary">{connectionStatus.text}</Badge>
          </div>
        </div>

        <div className="p-3 border-b sticky top-0 bg-slate-50/95 z-10 dark:bg-slate-950/95 dark:border-slate-800">
          <div className="relative">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search inbox..."
              className="pl-9 bg-white dark:bg-slate-900"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        
        <div className="flex-1 min-h-0 overflow-hidden">
          <ScrollArea className="h-full">
            {isLoading.contacts ? (
              <div className="space-y-2 p-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="flex items-center gap-3 p-3">
                    <div className="h-10 w-10 rounded-full bg-muted animate-pulse" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 w-3/4 bg-muted rounded animate-pulse" />
                      <div className="h-3 w-1/2 bg-muted rounded animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            ) : filteredContacts.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full p-6 text-center">
                <FiUsers className="h-12 w-12 mb-4 text-muted-foreground/30" />
                <p className="text-muted-foreground">No inbox threads found</p>
                <p className="text-sm text-muted-foreground/70 mt-1">
                  {searchTerm || showNeedsAttentionOnly ? 'Try a different filter' : 'Start by adding contacts'}
                </p>
              </div>
            ) : (
              filteredContacts.map(contact => (
                <ContactListItem
                  key={contact.id}
                  contact={contact}
                  isSelected={selectedContact?.id === contact.id}
                  onSelect={setSelectedContact}
                  hasUnread={contact.unread_count > 0}
                />
              ))
            )}
          </ScrollArea>
        </div>
      </div>

      {/* Messages Panel */}
      {selectedContact ? (
        <div className="flex-1 flex flex-col bg-white h-full dark:bg-slate-900">
          <div className="p-4 border-b border-slate-200 flex items-center justify-between sticky top-0 bg-white/95 z-10 dark:bg-slate-900/95 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => setSelectedContact(null)}
                className="md:hidden"
              >
                <FiArrowLeft className="h-5 w-5" />
              </Button>
              <Avatar>
                <AvatarImage src={`https://ui-avatars.com/api/?name=${encodeURIComponent(selectedContact.name || selectedContact.whatsapp_id)}`} />
                <AvatarFallback>{selectedContact.name?.substring(0,2) || 'CN'}</AvatarFallback>
              </Avatar>
              <div>
                <h2 className="font-semibold">{selectedContact.name || selectedContact.whatsapp_id}</h2>
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="text-xs text-muted-foreground">
                    {selectedContact.last_seen ? 
                      `Active ${formatDistanceToNow(parseISO(selectedContact.last_seen), { addSuffix: true })}` : 
                      'Offline'}
                  </p>
                  <div className="flex items-center gap-1.5">
                    <span className={`h-1.5 w-1.5 rounded-full ${connectionStatus.bgColor}`}></span>
                    <span className={`text-xs ${connectionStatus.color}`}>{connectionStatus.text}</span>
                  </div>
                  {selectedContact.unread_count > 0 && <Badge className="bg-cyan-600 text-white hover:bg-cyan-600">{selectedContact.unread_count} unread</Badge>}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {canManageAutomation && (
                <Button
                  type="button"
                  variant="outline"
                  className="hidden sm:inline-flex"
                  onClick={handleToggleIntervention}
                >
                  {selectedContact.needs_human_intervention ? 'Re-enable Bot' : 'Pause Bot'}
                </Button>
              )}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <FiMoreVertical className="h-5 w-5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem>View profile</DropdownMenuItem>
                  <DropdownMenuItem>Mark as unread</DropdownMenuItem>
                  {canManageAutomation && <DropdownMenuItem onClick={handleToggleIntervention}>{selectedContact.needs_human_intervention ? 'Re-enable Bot' : 'Pause Bot'}</DropdownMenuItem>}
                  <DropdownMenuItem className="text-destructive">Delete chat</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          {/* Intervention Banner */}
          {selectedContact.needs_human_intervention && (
            <div className="bg-yellow-100 dark:bg-yellow-900/30 border-b border-yellow-300 dark:border-yellow-700 p-2 flex items-center justify-between gap-4 text-sm">
                <div className="flex items-center gap-2">
                    <FiAlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 shrink-0" />
                    <p className="font-medium text-yellow-800 dark:text-yellow-200">
                        Automated responses are paused.
                    </p>
                </div>
                <Button 
                    variant="outline" 
                    size="sm" 
                    className="bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-yellow-800 dark:text-yellow-200 border-yellow-300 dark:border-yellow-600 hover:text-yellow-900 dark:hover:text-yellow-100"
                    onClick={handleToggleIntervention}
                    disabled={!canManageAutomation}
                >
                    Re-enable Bot
                </Button>
            </div>
          )}
          
          {/* Message List Area */}
          <div className="flex-1 min-h-0 overflow-hidden bg-linear-to-b from-slate-50 to-cyan-50/40 dark:from-slate-950 dark:to-slate-900">
            {isLoading.messages ? (
              <div className="flex justify-center items-center h-full">
                <FiLoader className="animate-spin h-6 w-6 text-muted-foreground" />
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <FiMessageSquare className="h-12 w-12 mb-4 opacity-30" />
                <h3 className="text-lg font-medium">No messages yet</h3>
                <p className="text-sm mt-1">Send your first message to {selectedContact.name || 'this contact'}</p>
              </div>
            ) : (
              <ScrollArea className="h-full p-4 md:p-6">
                <div className="space-y-3">
                  {messages.map((msg, i) => (
                    <MessageBubble 
                      key={msg.id} 
                      message={msg} 
                      contactName={selectedContact.name}
                      isLast={i === messages.length - 1}
                    />
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>
            )}
          </div>

          <div className="p-4 border-t border-slate-200 bg-white sticky bottom-0 dark:bg-slate-900 dark:border-slate-800">
            {!canReply && (
              <div className="mb-3 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950/30 dark:text-amber-200">
                Your role can view the inbox, but it cannot send replies.
              </div>
            )}
            <form onSubmit={handleSendMessage} className="flex items-end gap-2">
              <Button 
                type="button" 
                variant="ghost" 
                size="icon"
                className="text-muted-foreground"
                disabled={!canReply}
              >
                <FiPaperclip className="h-5 w-5" />
              </Button>
              <Textarea
                ref={inputRef}
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={readyState !== ReadyState.OPEN || !canReply}
                placeholder={canReply ? 'Reply in realtime...' : 'Reply permission required'}
                rows={1}
                className="flex-1 py-3 min-h-11 max-h-[120px] overflow-y-auto resize-none rounded-2xl border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-950"
              />
              <Button 
                type="submit" 
                size="sm" 
                disabled={!newMessage.trim() || readyState !== ReadyState.OPEN || !canReply}
                className="h-11 bg-cyan-600 text-white hover:bg-cyan-700"
              >
                <FiSend className="h-4 w-4" />
              </Button>
            </form>
          </div>
        </div>
      ) : (
        <div className="hidden md:flex flex-1 flex-col items-center justify-center p-10 text-center text-muted-foreground bg-linear-to-br from-white to-cyan-50 dark:from-slate-900 dark:to-slate-950">
          <FiMessageSquare className="h-24 w-24 mb-4 opacity-20" />
          <h3 className="text-xl font-medium mb-2">Select an inbox thread</h3>
          <p className="max-w-md text-sm">
            Choose a live conversation to review messages, respond in realtime, and manage bot handover.
          </p>
        </div>
      )}
    </div>
  );
}