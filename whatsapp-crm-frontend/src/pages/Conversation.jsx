// src/pages/Conversation.jsx — WhatsApp inbox
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAtom } from 'jotai';
import { toast } from 'sonner';
import { useDebounce } from 'use-debounce';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { differenceInHours, isSameDay, parseISO } from 'date-fns';
import {
  FiAlertCircle, FiArrowLeft, FiArrowRight, FiCheck, FiClock, FiList, FiMessageSquare, FiMoreVertical,
  FiPauseCircle, FiPlayCircle, FiSearch, FiSend, FiUser,
} from 'react-icons/fi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import InitialsAvatar from '@/components/app/InitialsAvatar';
import { EmptyState, LoadingState } from '@/components/app/States';
import { contactsApi, API_BASE_URL } from '@/lib/api';
import { selectedContactAtom } from '@/atoms/conversationAtoms';
import { useAuth } from '@/context/AuthContext';
import { APP_ROLES, hasPermission, hasRole } from '@/lib/rbac';
import { normalizeToken } from '@/services/auth';
import { formatDate, formatRelative } from '@/lib/format';

const CONNECTION = {
  [ReadyState.CONNECTING]: { text: 'Connecting…', dot: 'bg-warning' },
  [ReadyState.OPEN]: { text: 'Live', dot: 'bg-success' },
  [ReadyState.CLOSING]: { text: 'Disconnecting…', dot: 'bg-warning' },
  [ReadyState.CLOSED]: { text: 'Disconnected', dot: 'bg-destructive' },
  [ReadyState.UNINSTANTIATED]: { text: 'Not connected', dot: 'bg-muted-foreground' },
};

function InteractiveContent({ payload }) {
  const interactive = payload?.interactive;
  if (!interactive) return <span className="italic opacity-80">[Interactive message]</span>;
  const { type, header, body, footer, action, button_reply: buttonReply, list_reply: listReply } = interactive;
  if (type === 'button_reply' || type === 'list_reply') {
    const reply = buttonReply || listReply || {};
    return (
      <span className="flex items-center gap-1.5">
        <FiArrowRight className="size-3.5 shrink-0 opacity-70" aria-hidden /> {reply.title}
      </span>
    );
  }
  return (
    <div className="space-y-1.5">
      {header?.type === 'text' && <p className="font-semibold">{header.text}</p>}
      {body?.text && <p className="whitespace-pre-wrap">{body.text}</p>}
      {footer?.text && <p className="text-xs opacity-75">{footer.text}</p>}
      {type === 'button' && action?.buttons?.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {action.buttons.map((b) => (
            <span key={b.reply?.id} className="rounded-md border border-current/25 px-2 py-0.5 text-xs">{b.reply?.title}</span>
          ))}
        </div>
      )}
      {type === 'list' && <span className="flex items-center gap-1 pt-1 text-xs opacity-80"><FiList className="size-3.5" /> {action?.button || 'Options'}</span>}
    </div>
  );
}

const STATUS_ICON = {
  sent: <FiCheck className="size-3" aria-label="Sent" />,
  delivered: <span className="flex" aria-label="Delivered"><FiCheck className="size-3" /><FiCheck className="-ml-1.5 size-3" /></span>,
  read: <span className="flex text-info" aria-label="Read"><FiCheck className="size-3" /><FiCheck className="-ml-1.5 size-3" /></span>,
  failed: <FiAlertCircle className="size-3 text-destructive" aria-label="Failed" />,
  pending: <FiClock className="size-3" aria-label="Pending" />,
};

function MessageBubble({ message }) {
  const outgoing = message.direction === 'out';
  return (
    <div className={`flex ${outgoing ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-3.5 py-2 text-sm shadow-xs ${outgoing
          ? 'rounded-br-sm bg-primary text-primary-foreground'
          : 'rounded-bl-sm border bg-card text-card-foreground'}`}
        title={message.timestamp ? new Date(message.timestamp).toLocaleString() : ''}
      >
        {message.is_internal_note && <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide opacity-75">Internal note</p>}
        <div className="break-words">
          {message.message_type === 'interactive' ? <InteractiveContent payload={message.content_payload} />
            : message.text_content ? <p className="whitespace-pre-wrap">{message.text_content}</p>
              : <p className="italic opacity-80">{message.content_preview || `[${message.message_type_display || message.message_type}]`}</p>}
        </div>
        <div className={`mt-1 flex items-center justify-end gap-1 text-[11px] ${outgoing ? 'text-primary-foreground/75' : 'text-muted-foreground'}`}>
          <span>{message.timestamp ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Sending…'}</span>
          {outgoing && STATUS_ICON[message.status]}
        </div>
      </div>
    </div>
  );
}

function ThreadItem({ contact, selected, onSelect }) {
  const name = contact.name || contact.whatsapp_id;
  return (
    <button
      type="button"
      onClick={() => onSelect(contact)}
      className={`flex w-full items-center gap-3 border-l-[3px] px-3 py-3 text-left transition-colors ${selected
        ? 'border-l-brand-accent bg-accent'
        : 'border-l-transparent hover:bg-muted/60'}`}
      aria-current={selected ? 'true' : undefined}
    >
      <InitialsAvatar name={name} />
      <span className="min-w-0 flex-1">
        <span className="flex items-center justify-between gap-2">
          <span className="truncate font-medium">{name}</span>
          <span className="shrink-0 text-[11px] text-muted-foreground">{contact.last_seen ? formatRelative(contact.last_seen).replace('about ', '') : ''}</span>
        </span>
        <span className="flex items-center justify-between gap-2">
          <span className="truncate text-xs text-muted-foreground">{contact.last_message_preview || 'No messages yet'}</span>
          <span className="flex shrink-0 items-center gap-1">
            {contact.needs_human_intervention && <FiAlertCircle className="size-3.5 text-warning" aria-label="Needs a human" />}
            {contact.unread_count > 0 && (
              <span className="min-w-5 rounded-full bg-brand-accent px-1.5 text-center text-[11px] font-semibold text-white">{contact.unread_count}</span>
            )}
          </span>
        </span>
      </span>
    </button>
  );
}

export default function ConversationsPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [contacts, setContacts] = useState([]);
  const [selectedContact, setSelectedContact] = useAtom(selectedContactAtom);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [attentionOnly, setAttentionOnly] = useState(searchParams.get('filter') === 'attention');
  const [loading, setLoading] = useState({ contacts: true, messages: false });
  const [search, setSearch] = useState('');
  const [debouncedSearch] = useDebounce(search, 300);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const { accessToken, user } = useAuth();

  const canManageAutomation = hasRole(user, [APP_ROLES.ADMIN, APP_ROLES.MANAGER]);
  const canReply = hasPermission(user, ['conversations.add_message'])
    || hasRole(user, [APP_ROLES.ADMIN, APP_ROLES.MANAGER, APP_ROLES.AGENT]);

  // Pass a URL or null (idle). A function returning null makes the library log
  // "Failed to get a valid URL".
  const wsToken = normalizeToken(accessToken);
  const socketUrl = selectedContact?.id && /^[\w-]+\.[\w-]+\.[\w-]+$/.test(wsToken)
    ? `${API_BASE_URL.replace(/^http/, 'ws')}/ws/conversations/${selectedContact.id}/?token=${wsToken}`
    : null;
  const { sendJsonMessage, lastJsonMessage, readyState } = useWebSocket(socketUrl, {
    shouldReconnect: () => true,
    reconnectAttempts: 20,
    reconnectInterval: (attempt) => Math.min(1000 * 2 ** attempt, 15000),
  }, Boolean(socketUrl));
  const connection = CONNECTION[readyState];
  const live = readyState === ReadyState.OPEN;

  const fetchContacts = useCallback(async () => {
    setLoading((l) => ({ ...l, contacts: true }));
    try {
      const res = await contactsApi.list({
        search: debouncedSearch || undefined,
        needs_human_intervention: attentionOnly ? 'true' : undefined,
        page_size: 100,
      });
      setContacts(res.data.results || res.data || []);
    } catch {
      toast.error("Couldn't load conversations");
    } finally {
      setLoading((l) => ({ ...l, contacts: false }));
    }
  }, [debouncedSearch, attentionOnly]);

  useEffect(() => { fetchContacts(); }, [fetchContacts]);

  // Deep link from Contacts: /conversation?contactId=12
  useEffect(() => {
    const id = Number(searchParams.get('contactId'));
    if (!id || selectedContact?.id === id) return;
    contactsApi.retrieve(id)
      .then((res) => setSelectedContact(res.data))
      .catch(() => toast.error('That conversation could not be found.'));
  }, [searchParams, selectedContact?.id, setSelectedContact]);

  const selectContact = (contact) => {
    setSelectedContact(contact);
    const next = new URLSearchParams(searchParams);
    if (contact) next.set('contactId', contact.id); else next.delete('contactId');
    setSearchParams(next, { replace: true });
  };

  useEffect(() => {
    if (!selectedContact?.id) { setMessages([]); return; }
    let cancelled = false;
    setLoading((l) => ({ ...l, messages: true }));
    const contactId = selectedContact.id;
    contactsApi.listMessages(contactId, { page_size: 100 })
      .then((res) => {
        if (cancelled) return;
        setMessages([...(res.data.results || res.data || [])].reverse());
        // Opening a thread reads it: clear the unread badge locally and on the server.
        setContacts((list) => list.map((c) => (c.id === contactId ? { ...c, unread_count: 0 } : c)));
        contactsApi.markRead(contactId).catch(() => {});
      })
      .catch(() => toast.error("Couldn't load messages"))
      .finally(() => { if (!cancelled) setLoading((l) => ({ ...l, messages: false })); });
    inputRef.current?.focus();
    return () => { cancelled = true; };
  }, [selectedContact?.id]);

  useEffect(() => {
    if (!lastJsonMessage) return;
    const { type, message, contact: updated } = lastJsonMessage;
    if (type === 'new_message' && message) {
      setMessages((prev) => {
        const i = prev.findIndex((m) => m.id === message.id);
        if (i === -1) return [...prev, message];
        const next = [...prev];
        next[i] = message;
        return next;
      });
    } else if (type === 'contact_updated' && updated && selectedContact?.id === updated.id) {
      setSelectedContact((c) => ({ ...c, ...updated }));
      setContacts((list) => list.map((c) => (c.id === updated.id ? { ...c, ...updated } : c)));
    }
  }, [lastJsonMessage, selectedContact?.id, setSelectedContact]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ block: 'end' });
  }, [messages]);

  const stats = useMemo(() => ({
    unread: contacts.filter((c) => c.unread_count > 0).length,
    attention: contacts.filter((c) => c.needs_human_intervention).length,
  }), [contacts]);

  // WhatsApp only allows free-form replies within 24h of the customer's last message.
  const lastIncoming = [...messages].reverse().find((m) => m.direction === 'in');
  const outsideWindow = lastIncoming?.timestamp && differenceInHours(new Date(), parseISO(lastIncoming.timestamp)) >= 24;

  const send = (e) => {
    e?.preventDefault();
    const text = draft.trim();
    if (!text || !selectedContact) return;
    if (!live) {
      toast.error('Not connected — wait for the connection to come back, then send again.');
      return;
    }
    sendJsonMessage({ type: 'send_message', message: text });
    setDraft('');
  };

  const toggleBot = () => {
    if (!live) { toast.error('Not connected — try again in a moment.'); return; }
    sendJsonMessage({ type: 'toggle_intervention' });
  };

  return (
    <div className="-my-2 flex h-[calc(100dvh-9.5rem)] min-h-[480px] overflow-hidden rounded-xl border bg-card">
      {/* Thread list */}
      <section className={`${selectedContact ? 'hidden md:flex' : 'flex'} w-full flex-col border-r md:w-80 lg:w-96`} aria-label="Conversations">
        <div className="space-y-3 border-b p-3">
          <div className="flex items-center justify-between gap-2">
            <h2 className="font-semibold">Inbox</h2>
            <span className="text-xs text-muted-foreground">{contacts.length} conversations · {stats.unread} unread</span>
          </div>
          <div className="relative">
            <FiSearch className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
            <Input placeholder="Search name or number…" className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search conversations" />
          </div>
          <div className="flex gap-1">
            <Button size="sm" variant={!attentionOnly ? 'secondary' : 'ghost'} onClick={() => setAttentionOnly(false)}>All</Button>
            <Button size="sm" variant={attentionOnly ? 'secondary' : 'ghost'} onClick={() => setAttentionOnly(true)}>
              Needs a human {stats.attention > 0 && !attentionOnly && <span className="ml-1 rounded-full bg-warning/20 px-1.5 text-xs">{stats.attention}</span>}
            </Button>
          </div>
        </div>
        <div className="flex-1 divide-y overflow-y-auto">
          {loading.contacts && contacts.length === 0 ? <LoadingState label="Loading conversations…" /> : contacts.length === 0 ? (
            <EmptyState
              icon={FiMessageSquare}
              title={attentionOnly ? 'Nobody is waiting for a human' : search ? 'No conversations match' : 'No conversations yet'}
              description={attentionOnly ? 'Customers the bot hands over will appear here.' : 'Messages to your WhatsApp number appear here.'}
            />
          ) : contacts.map((c) => (
            <ThreadItem key={c.id} contact={c} selected={selectedContact?.id === c.id} onSelect={selectContact} />
          ))}
        </div>
      </section>

      {/* Thread */}
      {selectedContact ? (
        <section className="flex min-w-0 flex-1 flex-col" aria-label={`Conversation with ${selectedContact.name || selectedContact.whatsapp_id}`}>
          <header className="flex items-center gap-3 border-b px-3 py-2.5">
            <Button variant="ghost" size="icon" className="md:hidden" onClick={() => selectContact(null)} aria-label="Back to conversations">
              <FiArrowLeft className="size-5" />
            </Button>
            <InitialsAvatar name={selectedContact.name || selectedContact.whatsapp_id} />
            <div className="min-w-0 flex-1">
              <p className="truncate font-semibold">{selectedContact.name || selectedContact.whatsapp_id}</p>
              <p className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>{selectedContact.whatsapp_id}</span>
                <span className="flex items-center gap-1"><span className={`size-1.5 rounded-full ${connection.dot}`} /> {connection.text}</span>
              </p>
            </div>
            {canManageAutomation && (
              <Button variant="outline" size="sm" className="hidden sm:inline-flex" onClick={toggleBot} disabled={!live}>
                {selectedContact.needs_human_intervention ? <><FiPlayCircle /> Resume bot</> : <><FiPauseCircle /> Pause bot</>}
              </Button>
            )}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Conversation actions"><FiMoreVertical className="size-5" /></Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => navigate(`/contacts?contactId=${selectedContact.id}`)}>
                  <FiUser className="size-4" /> View contact & bookings
                </DropdownMenuItem>
                {canManageAutomation && (
                  <DropdownMenuItem onClick={toggleBot} disabled={!live}>
                    {selectedContact.needs_human_intervention ? <><FiPlayCircle className="size-4" /> Resume bot</> : <><FiPauseCircle className="size-4" /> Pause bot</>}
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </header>

          {selectedContact.needs_human_intervention && (
            <div className="flex items-center gap-3 border-b bg-warning/10 px-4 py-2 text-sm">
              <FiAlertCircle className="size-4 shrink-0 text-warning" aria-hidden />
              <span className="flex-1">The bot is paused — you're handling this customer.</span>
              {canManageAutomation && <Button size="sm" variant="outline" onClick={toggleBot} disabled={!live}>Resume bot</Button>}
            </div>
          )}

          <div className="flex-1 overflow-y-auto bg-muted/30 px-3 py-4 sm:px-6">
            {loading.messages ? <LoadingState label="Loading messages…" /> : messages.length === 0 ? (
              <EmptyState icon={FiMessageSquare} title="No messages yet" description="When this customer messages you, the conversation appears here." />
            ) : (
              <div className="space-y-2">
                {messages.map((m, i) => {
                  const prev = messages[i - 1];
                  const newDay = m.timestamp && (!prev?.timestamp || !isSameDay(parseISO(prev.timestamp), parseISO(m.timestamp)));
                  return (
                    <React.Fragment key={m.id}>
                      {newDay && (
                        <div className="py-2 text-center">
                          <span className="rounded-full bg-background px-3 py-1 text-xs text-muted-foreground shadow-xs">{formatDate(m.timestamp, 'EEEE d MMM')}</span>
                        </div>
                      )}
                      <MessageBubble message={m} />
                    </React.Fragment>
                  );
                })}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          <footer className="border-t p-3">
            {!canReply ? (
              <p className="rounded-md bg-muted px-3 py-2 text-sm text-muted-foreground">Your role can read this inbox but can't reply.</p>
            ) : (
              <>
                {outsideWindow && (
                  <p className="mb-2 flex items-start gap-2 rounded-md bg-warning/10 px-3 py-2 text-xs">
                    <FiClock className="mt-0.5 size-3.5 shrink-0 text-warning" aria-hidden />
                    The customer last wrote over 24 hours ago. WhatsApp only delivers free-form replies inside the 24-hour window — use an approved template instead.
                  </p>
                )}
                <form onSubmit={send} className="flex items-end gap-2">
                  <Textarea
                    ref={inputRef}
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
                    placeholder={live ? 'Write a reply… (Enter to send, Shift+Enter for a new line)' : 'Connecting…'}
                    rows={1}
                    className="max-h-32 min-h-10 flex-1 resize-none"
                    aria-label="Reply"
                  />
                  <Button type="submit" size="icon" className="size-10" disabled={!draft.trim() || !live} aria-label="Send">
                    <FiSend className="size-4" />
                  </Button>
                </form>
              </>
            )}
          </footer>
        </section>
      ) : (
        <div className="hidden flex-1 md:flex">
          <EmptyState
            icon={FiMessageSquare}
            title="Select a conversation"
            description="Pick a customer on the left to read and reply. Use “Needs a human” to see customers the bot has handed over."
            className="m-auto"
          />
        </div>
      )}
    </div>
  );
}
