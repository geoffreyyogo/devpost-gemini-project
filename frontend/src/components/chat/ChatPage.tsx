'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Send, Loader2, Sprout, Plus, Trash2, Pencil, Check, X,
  MessageSquare, Bot, ChevronDown, ChevronRight, BrainCircuit,
  ImagePlus, XCircle, Smartphone, Globe, Phone,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/lib/api'
import type { Conversation, ConversationMessage } from '@/types'

// Channel icon helper
function ChannelBadge({ via }: { via: string }) {
  const icons: Record<string, { icon: typeof Globe; label: string; color: string }> = {
    web:  { icon: Globe, label: 'Web', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300' },
    ussd: { icon: Phone, label: 'USSD', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300' },
    sms:  { icon: Smartphone, label: 'SMS', color: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' },
  }
  const info = icons[via] || icons.web
  const Icon = info.icon
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${info.color}`}>
      <Icon className="h-3 w-3" /> {info.label}
    </span>
  )
}

export function ChatPage() {
  const { farmer } = useAuthStore()

  // Conversation list
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConvId, setActiveConvId] = useState<string | null>(null)
  const [loadingConvs, setLoadingConvs] = useState(true)

  // Messages for active conversation
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [loadingMsgs, setLoadingMsgs] = useState(false)

  // Input
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Reasoning toggle
  const [expandedReasoning, setExpandedReasoning] = useState<Set<number>>(new Set())

  // Rename state
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')

  // Mobile sidebar toggle
  const [showSidebar, setShowSidebar] = useState(false)

  // Load conversations on mount
  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = useCallback(async () => {
    setLoadingConvs(true)
    try {
      const data = await api.getConversations()
      setConversations(data)
      // Auto-select first conversation if none selected
      if (data.length > 0 && !activeConvId) {
        setActiveConvId(data[0].id)
      }
    } catch (err) {
      console.error('Failed to load conversations:', err)
    } finally {
      setLoadingConvs(false)
    }
  }, [activeConvId])

  // Load messages when active conversation changes
  useEffect(() => {
    if (!activeConvId) {
      setMessages([])
      return
    }
    loadMessages(activeConvId)
  }, [activeConvId])

  const loadMessages = async (convId: string) => {
    setLoadingMsgs(true)
    try {
      const data = await api.getConversationMessages(convId)
      setMessages(data)
    } catch (err) {
      console.error('Failed to load messages:', err)
    } finally {
      setLoadingMsgs(false)
    }
  }

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Image handling
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedImage(file)
      setImagePreview(URL.createObjectURL(file))
    }
  }

  const clearImage = () => {
    setSelectedImage(null)
    setImagePreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  // Send message
  const handleSend = async () => {
    const text = input.trim()
    if (!text && !selectedImage) return
    if (sending) return

    setSending(true)
    const userMsg = text || '(image attached)'

    // Optimistically add user message
    const tempMsg: ConversationMessage = {
      id: Date.now(),
      role: 'user',
      message: userMsg,
      via: 'web',
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, tempMsg])
    setInput('')

    try {
      let result: { reply: string; reasoning?: string | null; conversation_id?: string }

      if (selectedImage) {
        const res = await api.sendChatMessageWithImage(userMsg, selectedImage, activeConvId || undefined)
        result = res
        clearImage()
      } else {
        result = await api.sendChatMessage(userMsg, [], activeConvId || undefined)
      }

      // If this was a new conversation (no activeConvId), set the returned one
      if (result.conversation_id && !activeConvId) {
        setActiveConvId(result.conversation_id)
      } else if (result.conversation_id && result.conversation_id !== activeConvId) {
        setActiveConvId(result.conversation_id)
      }

      // Add assistant response
      const assistantMsg: ConversationMessage = {
        id: Date.now() + 1,
        role: 'user', // DB stores as user with response field
        message: userMsg,
        response: result.reply,
        reasoning: result.reasoning,
        via: 'web',
        timestamp: new Date().toISOString(),
      }
      // Replace temp user msg + add response
      setMessages(prev => {
        const withoutTemp = prev.filter(m => m.id !== tempMsg.id)
        return [...withoutTemp, assistantMsg]
      })

      // Refresh conversation list to update last message preview
      loadConversations()

    } catch (err) {
      console.error('Chat error:', err)
      const errorMsg: ConversationMessage = {
        id: Date.now() + 2,
        role: 'user',
        message: userMsg,
        response: 'Sorry, something went wrong. Please try again.',
        via: 'web',
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => {
        const withoutTemp = prev.filter(m => m.id !== tempMsg.id)
        return [...withoutTemp, errorMsg]
      })
    } finally {
      setSending(false)
    }
  }

  // New conversation
  const handleNewConversation = async () => {
    setActiveConvId(null)
    setMessages([])
    setShowSidebar(false)
  }

  // Delete conversation
  const handleDelete = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await api.deleteConversation(convId)
      setConversations(prev => prev.filter(c => c.id !== convId))
      if (activeConvId === convId) {
        setActiveConvId(null)
        setMessages([])
      }
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  // Rename conversation
  const startRename = (convId: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setRenamingId(convId)
    setRenameValue(currentTitle)
  }

  const confirmRename = async (convId: string) => {
    if (!renameValue.trim()) return
    try {
      await api.updateConversationTitle(convId, renameValue.trim())
      setConversations(prev =>
        prev.map(c => c.id === convId ? { ...c, title: renameValue.trim() } : c)
      )
    } catch (err) {
      console.error('Rename failed:', err)
    }
    setRenamingId(null)
  }

  const toggleReasoning = (id: number) => {
    setExpandedReasoning(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const formatTime = (ts: string) => {
    const d = new Date(ts)
    const now = new Date()
    const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000)
    if (diffDays === 0) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return d.toLocaleDateString([], { weekday: 'short' })
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
  }

  return (
    <div className="flex h-[calc(100vh-180px)] min-h-[500px] bg-gradient-to-br from-white to-gray-50 dark:from-gray-950 dark:to-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-xl">
      {/* ====== Conversation Sidebar ====== */}
      <div className={`
        ${showSidebar ? 'translate-x-0' : '-translate-x-full'}
        md:translate-x-0 absolute md:relative z-20
        w-72 h-full flex flex-col border-r border-gray-200 dark:border-gray-800
        bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-950 transition-transform duration-200
      `}>
        {/* Sidebar Header */}
        <div className="p-3 border-b border-gray-200 dark:border-gray-800 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/30 dark:to-emerald-950/30">
          <Button
            onClick={handleNewConversation}
            className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white gap-2 shadow-md shadow-green-200 dark:shadow-green-900/30"
            size="sm"
          >
            <Plus className="h-4 w-4" /> New Chat
          </Button>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {loadingConvs ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
            </div>
          ) : conversations.length === 0 ? (
            <div className="text-center py-8 px-4">
              <MessageSquare className="h-8 w-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
              <p className="text-sm text-gray-500 dark:text-gray-400">No conversations yet</p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Start chatting with Flora!</p>
            </div>
          ) : (
            conversations.map(conv => (
              <div
                key={conv.id}
                onClick={() => { setActiveConvId(conv.id); setShowSidebar(false) }}
                className={`group flex items-start gap-2 p-2.5 rounded-lg cursor-pointer transition-all text-sm ${
                  activeConvId === conv.id
                    ? 'bg-green-100 dark:bg-green-900/40 border border-green-200 dark:border-green-800'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                <MessageSquare className="h-4 w-4 mt-0.5 flex-shrink-0 text-gray-400" />
                <div className="flex-1 min-w-0">
                  {renamingId === conv.id ? (
                    <div className="flex items-center gap-1">
                      <Input
                        value={renameValue}
                        onChange={e => setRenameValue(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && confirmRename(conv.id)}
                        className="h-6 text-xs"
                        autoFocus
                        onClick={e => e.stopPropagation()}
                      />
                      <Button size="icon" variant="ghost" className="h-6 w-6" onClick={(e) => { e.stopPropagation(); confirmRename(conv.id) }}>
                        <Check className="h-3 w-3" />
                      </Button>
                      <Button size="icon" variant="ghost" className="h-6 w-6" onClick={(e) => { e.stopPropagation(); setRenamingId(null) }}>
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  ) : (
                    <>
                      <p className="font-medium truncate text-gray-800 dark:text-gray-200">
                        {conv.title}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] text-gray-400">{formatTime(conv.updated_at)}</span>
                        <ChannelBadge via={conv.channel} />
                        {conv.message_count > 0 && (
                          <span className="text-[10px] text-gray-400">{conv.message_count} msgs</span>
                        )}
                      </div>
                    </>
                  )}
                </div>
                {/* Actions */}
                {renamingId !== conv.id && (
                  <div className="hidden group-hover:flex items-center gap-0.5 flex-shrink-0">
                    <button
                      onClick={(e) => startRename(conv.id, conv.title, e)}
                      className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
                    >
                      <Pencil className="h-3 w-3 text-gray-400" />
                    </button>
                    <button
                      onClick={(e) => handleDelete(conv.id, e)}
                      className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30"
                    >
                      <Trash2 className="h-3 w-3 text-red-400" />
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* ====== Main Chat Area ====== */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat Header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 dark:border-gray-800 bg-gradient-to-r from-green-50/80 via-emerald-50/60 to-transparent dark:from-green-950/40 dark:via-emerald-950/20 dark:to-transparent backdrop-blur-sm">
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className="md:hidden p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <MessageSquare className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-full bg-gradient-to-br from-green-400 to-emerald-600 flex items-center justify-center shadow-md shadow-green-200 dark:shadow-green-900/30">
              <Sprout className="h-4.5 w-4.5 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-gray-900 dark:text-white">Flora AI</h3>
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
                <p className="text-xs text-gray-500">Online • Your agricultural advisor</p>
              </div>
            </div>
          </div>
          {activeConvId && (
            <Badge variant="outline" className="ml-auto text-[10px]">
              {conversations.find(c => c.id === activeConvId)?.title || 'Chat'}
            </Badge>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5" style={{ backgroundImage: 'radial-gradient(circle at 50% 50%, rgba(34,197,94,0.03) 0%, transparent 70%)' }}>
          {!activeConvId && messages.length === 0 && !loadingMsgs && (
            <div className="flex flex-col items-center justify-center h-full text-center px-6">
              <div className="relative mb-6">
                <div className="h-20 w-20 rounded-full bg-gradient-to-br from-green-100 to-emerald-200 dark:from-green-900/40 dark:to-emerald-800/40 flex items-center justify-center shadow-lg shadow-green-100 dark:shadow-green-900/20">
                  <Sprout className="h-10 w-10 text-green-600 dark:text-green-400" />
                </div>
                <div className="absolute -bottom-1 -right-1 h-6 w-6 rounded-full bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center shadow-sm">
                  <span className="text-white text-xs">✨</span>
                </div>
              </div>
              <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-2">
                Chat with Flora AI
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md leading-relaxed">
                Ask me anything about your farm — crop health, soil management, weather advice, bloom predictions, or pest control.
                {farmer?.name && ` I have access to your farm data, ${farmer.name.split(' ')[0]}! 🌾`}
              </p>
              <div className="grid grid-cols-2 gap-2 mt-6 max-w-lg">
                {[
                  { q: 'My maize leaves are yellowing', icon: '🌽' },
                  { q: 'When should I plant beans?', icon: '🫘' },
                  { q: 'How is the bloom outlook?', icon: '🌺' },
                  { q: 'Soil pH is 5.0, what do I do?', icon: '🧪' },
                ].map(({ q, icon }) => (
                  <button
                    key={q}
                    onClick={() => { setInput(q) }}
                    className="flex items-center gap-2 px-3 py-2.5 text-xs text-left rounded-xl border border-gray-200 dark:border-gray-700 hover:bg-gradient-to-r hover:from-green-50 hover:to-emerald-50 dark:hover:from-green-950/30 dark:hover:to-emerald-950/30 hover:border-green-300 dark:hover:border-green-700 text-gray-600 dark:text-gray-400 transition-all hover:shadow-sm"
                  >
                    <span className="text-base flex-shrink-0">{icon}</span>
                    <span>{q}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {loadingMsgs && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-green-500" />
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className="space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
              {/* User message */}
              <div className="flex justify-end">
                <div className="max-w-[80%] bg-gradient-to-br from-green-500 to-emerald-600 text-white rounded-2xl rounded-br-sm px-4 py-3 shadow-md shadow-green-200/50 dark:shadow-green-900/30">
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.message}</p>
                  <div className="flex items-center gap-2 mt-1.5 justify-end">
                    <span className="text-[10px] opacity-60">{formatTime(msg.timestamp)}</span>
                    {msg.via && msg.via !== 'web' && <ChannelBadge via={msg.via} />}
                  </div>
                </div>
              </div>

              {/* Assistant response */}
              {msg.response && (
                <div className="flex justify-start gap-2.5">
                  <div className="flex-shrink-0 h-8 w-8 rounded-full bg-gradient-to-br from-green-100 to-emerald-200 dark:from-green-900/50 dark:to-emerald-900/50 flex items-center justify-center mt-1 shadow-sm">
                    <Bot className="h-4 w-4 text-green-700 dark:text-green-400" />
                  </div>
                  <div className="max-w-[80%]">
                    <div className="bg-white dark:bg-gray-800/80 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm border border-gray-100 dark:border-gray-700/50">
                      <div className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed space-y-1.5">
                        {msg.response.split('\n').map((line, i) => {
                          // Headers (bold lines)
                          if (line.startsWith('**') && line.endsWith('**')) {
                            return <p key={i} className="font-bold text-gray-900 dark:text-gray-100 mt-3 mb-1 text-[15px]">{line.replace(/\*\*/g, '')}</p>
                          }
                          // Inline bold
                          if (line.includes('**')) {
                            const parts = line.split(/\*\*(.*?)\*\*/g)
                            return (
                              <p key={i}>
                                {parts.map((part, j) =>
                                  j % 2 === 1 ? <strong key={j} className="font-semibold text-gray-900 dark:text-gray-100">{part}</strong> : <span key={j}>{part}</span>
                                )}
                              </p>
                            )
                          }
                          // Bullet points
                          if (/^[\*•\-]\s+/.test(line)) {
                            return (
                              <div key={i} className="flex items-start gap-2 ml-1 py-0.5">
                                <span className="text-green-500 mt-0.5 flex-shrink-0">•</span>
                                <span>{line.replace(/^[\*•\-]\s+/, '')}</span>
                              </div>
                            )
                          }
                          // Numbered items
                          if (/^\d+\.\s/.test(line)) {
                            const num = line.match(/^(\d+)\./)?.[1]
                            return (
                              <div key={i} className="flex items-start gap-2 ml-1 py-0.5">
                                <span className="text-green-600 font-bold text-xs bg-green-100 dark:bg-green-900/40 rounded-full w-5 h-5 flex items-center justify-center flex-shrink-0 mt-0.5">{num}</span>
                                <span>{line.replace(/^\d+\.\s/, '')}</span>
                              </div>
                            )
                          }
                          if (line.trim() === '') return <div key={i} className="h-1.5" />
                          return <p key={i}>{line}</p>
                        })}
                      </div>
                    </div>

                    {/* Reasoning toggle */}
                    {msg.reasoning && (
                      <div className="mt-2">
                        <button
                          onClick={() => toggleReasoning(msg.id)}
                          className="flex items-center gap-1.5 text-xs text-purple-600 dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-300 transition-colors group"
                        >
                          <BrainCircuit className="h-3.5 w-3.5 group-hover:animate-pulse" />
                          <span className="font-medium">Flora&apos;s Reasoning</span>
                          {expandedReasoning.has(msg.id) ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                        </button>
                        {expandedReasoning.has(msg.id) && (
                          <div className="mt-2 p-3.5 bg-gradient-to-br from-purple-50 to-violet-50 dark:from-purple-950/30 dark:to-violet-950/30 border border-purple-200 dark:border-purple-800 rounded-xl text-xs text-purple-900 dark:text-purple-200 whitespace-pre-wrap max-h-64 overflow-y-auto leading-relaxed shadow-inner">
                            {msg.reasoning}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}

          {sending && (
            <div className="flex justify-start gap-2.5 animate-in fade-in duration-300">
              <div className="flex-shrink-0 h-8 w-8 rounded-full bg-gradient-to-br from-green-100 to-emerald-200 dark:from-green-900/50 dark:to-emerald-900/50 flex items-center justify-center shadow-sm">
                <Bot className="h-4 w-4 text-green-700 dark:text-green-400" />
              </div>
              <div className="bg-white dark:bg-gray-800/80 rounded-2xl rounded-bl-sm px-5 py-3.5 flex items-center gap-3 shadow-sm border border-gray-100 dark:border-gray-700/50">
                <div className="flex gap-1">
                  <span className="h-2 w-2 bg-green-500 rounded-full animate-bounce [animation-delay:0ms]"></span>
                  <span className="h-2 w-2 bg-green-500 rounded-full animate-bounce [animation-delay:150ms]"></span>
                  <span className="h-2 w-2 bg-green-500 rounded-full animate-bounce [animation-delay:300ms]"></span>
                </div>
                <span className="text-sm text-gray-500 dark:text-gray-400 font-medium">Flora is thinking...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Image preview */}
        {imagePreview && (
          <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-800">
            <div className="relative inline-block">
              <img src={imagePreview} alt="Preview" className="h-16 w-16 object-cover rounded-lg border" />
              <button
                onClick={clearImage}
                className="absolute -top-1.5 -right-1.5 bg-red-500 text-white rounded-full p-0.5"
              >
                <XCircle className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* Input */}
        <div className="p-3 border-t border-gray-200 dark:border-gray-800 bg-gradient-to-r from-gray-50/80 to-white dark:from-gray-900/80 dark:to-gray-950">
          <div className="flex items-center gap-2 bg-white dark:bg-gray-800/80 rounded-xl border border-gray-200 dark:border-gray-700 px-2 py-1 shadow-sm focus-within:border-green-400 dark:focus-within:border-green-600 focus-within:ring-2 focus-within:ring-green-100 dark:focus-within:ring-green-900/30 transition-all">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageSelect}
              accept="image/*"
              className="hidden"
            />
            <Button
              variant="ghost"
              size="icon"
              onClick={() => fileInputRef.current?.click()}
              className="flex-shrink-0 text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg"
            >
              <ImagePlus className="h-5 w-5" />
            </Button>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Ask Flora anything about your farm..."
              disabled={sending}
              className="flex-1 bg-transparent border-none outline-none text-sm text-gray-800 dark:text-gray-200 placeholder:text-gray-400 dark:placeholder:text-gray-500 py-2"
            />
            <Button
              onClick={handleSend}
              disabled={sending || (!input.trim() && !selectedImage)}
              size="icon"
              className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white flex-shrink-0 rounded-lg shadow-md shadow-green-200/50 dark:shadow-green-900/30 disabled:opacity-40"
            >
              {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>
          <p className="text-[10px] text-center text-gray-400 dark:text-gray-500 mt-1.5">Flora AI can make mistakes. Verify important farming advice with a local expert.</p>
        </div>
      </div>
    </div>
  )
}
