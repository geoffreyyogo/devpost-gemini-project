'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { MessageSquare, X, Send, Loader2, Sprout, AlertCircle, Bot, ImagePlus, XCircle, ChevronDown, ChevronRight, BrainCircuit } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/lib/api'
import type { ChatMessage } from '@/types'
import ReactMarkdown from 'react-markdown'

interface FloraChatWidgetProps {
  initialOpen?: boolean
  onOpenChange?: (open: boolean) => void
}

export function FloraChatWidget({ initialOpen, onOpenChange }: FloraChatWidgetProps = {}) {
  const { farmer } = useAuthStore()
  const [isOpen, setIsOpen] = useState(false)

  // Sync with external open state
  useEffect(() => {
    if (initialOpen) {
      setIsOpen(true)
    }
  }, [initialOpen])

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    onOpenChange?.(open)
  }
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [floraAvailable, setFloraAvailable] = useState(true)
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [expandedReasoning, setExpandedReasoning] = useState<Set<number>>(new Set())
  const [conversationId, setConversationId] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Initialize with welcome message
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      const welcomeMessage: ChatMessage = {
        role: 'assistant',
        content: farmer 
          ? `Hi ${farmer.name.split(' ')[0]}! 👋 I'm Flora, your AI farming assistant. I can help you with crop advice, bloom predictions, weather insights, and more. How can I assist you today?`
          : `Hello! 👋 I'm Flora, your AI farming assistant. I'm here to help with crop advice, bloom predictions, and farming best practices. What would you like to know?`,
        timestamp: new Date().toISOString()
      }
      setMessages([welcomeMessage])
    }
  }, [isOpen, farmer])

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.type.startsWith('image/')) return
    if (file.size > 10 * 1024 * 1024) {
      alert('Image must be under 10MB')
      return
    }
    setSelectedImage(file)
    setImagePreview(URL.createObjectURL(file))
  }

  const clearImage = () => {
    setSelectedImage(null)
    if (imagePreview) URL.revokeObjectURL(imagePreview)
    setImagePreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleSendMessage = async () => {
    if ((!input.trim() && !selectedImage) || loading) return

    const messageText = input.trim() || (selectedImage ? "What's wrong with my crop?" : '')
    const userMessage: ChatMessage = {
      role: 'user',
      content: selectedImage ? `📷 [Image attached] ${messageText}` : messageText,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      let response: string
      let reasoning: string | null = null

      if (selectedImage) {
        // Send with image — uses disease classification + RAG
        const result = await api.sendChatMessageWithImage(messageText, selectedImage, conversationId || undefined)
        response = result.reply
        reasoning = result.reasoning || null
        if (result.conversation_id) setConversationId(result.conversation_id)

        // Show classification info if a disease was detected
        if (result.classification?.disease && result.classification.disease !== 'unknown' && result.classification.disease !== 'healthy') {
          const conf = (result.classification.confidence * 100).toFixed(0)
          response = `🔬 **Disease Detected:** ${result.classification.disease.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())} (${conf}% confidence)\n\n${response}`
        }

        clearImage()
      } else {
        // Text-only chat
        const result = await api.sendChatMessage(messageText, messages, conversationId || undefined)
        response = result.reply
        reasoning = result.reasoning || null
        if (result.conversation_id) setConversationId(result.conversation_id)
      }

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response,
        reasoning: reasoning,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, assistantMessage])
      setFloraAvailable(true)
    } catch (error: any) {
      console.error('Flora AI error:', error)
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: "I'm having trouble processing your request right now. Please try again in a moment.",
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <>
      {/* Floating Chat Button */}
      {!isOpen && (
        <button
          onClick={() => handleOpenChange(true)}
          className="fixed bottom-6 right-6 w-14 h-14 sm:w-16 sm:h-16 bg-gradient-to-br from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white rounded-full shadow-2xl hover:shadow-green-600/50 hover:scale-110 transition-all duration-300 z-50 flex items-center justify-center group"
          aria-label="Chat with Flora AI"
        >
          <MessageSquare className="h-7 w-7 group-hover:scale-110 transition-transform" />
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-pink-500 rounded-full animate-pulse" />
        </button>
      )}

      {/* Chat Modal */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-full max-w-md z-50 animate-in slide-in-from-bottom-5 duration-300 flora-modal-mobile">
          <Card className="shadow-2xl border-green-200 dark:border-green-800 h-full flex flex-col bg-white dark:bg-gray-900">
            <CardHeader className="bg-gradient-to-r from-green-600 to-green-700 text-white rounded-t-lg border-b border-green-500/20 shadow-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                    <Sprout className="h-6 w-6" />
                  </div>
                  <div>
                    <CardTitle className="text-white font-bold text-lg">Flora AI</CardTitle>
                    <CardDescription className="text-green-100 text-xs font-medium">
                      Your Agricultural Assistant
                    </CardDescription>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleOpenChange(false)}
                  className="text-white hover:bg-white/20"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>

            {!floraAvailable && (
              <div className="bg-yellow-50 dark:bg-yellow-950 border-b border-yellow-200 dark:border-yellow-800 p-3">
                <div className="flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-yellow-700 dark:text-yellow-300">
                    Flora AI is running in demo mode. Some features may be limited.
                  </p>
                </div>
              </div>
            )}

            <CardContent className="h-[400px] overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-gray-900">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-2 ${
                      message.role === 'user'
                        ? 'bg-green-600 text-white'
                        : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    {message.role === 'assistant' && (
                      <div className="flex items-center gap-2 mb-1">
                        <Bot className="h-4 w-4 text-green-600" />
                        <span className="text-xs font-semibold text-green-600">Flora</span>
                      </div>
                    )}
                    {message.role === 'user' ? (
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    ) : (
                      <div className="text-sm prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:my-2 prose-headings:text-green-700 dark:prose-headings:text-green-400 prose-strong:text-green-700 dark:prose-strong:text-green-400 prose-a:text-green-600">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                      </div>
                    )}
                    
                    {/* Collapsible reasoning toggle */}
                    {message.role === 'assistant' && message.reasoning && (
                      <div className="mt-2 border-t border-gray-200 dark:border-gray-700 pt-2">
                        <button
                          onClick={() => {
                            setExpandedReasoning(prev => {
                              const next = new Set(prev)
                              if (next.has(index)) next.delete(index)
                              else next.add(index)
                              return next
                            })
                          }}
                          className="flex items-center gap-1.5 text-xs text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 transition-colors font-medium"
                        >
                          <BrainCircuit className="h-3.5 w-3.5" />
                          {expandedReasoning.has(index) ? (
                            <>
                              <ChevronDown className="h-3 w-3" />
                              Hide Flora&apos;s Thinking
                            </>
                          ) : (
                            <>
                              <ChevronRight className="h-3 w-3" />
                              Read Flora&apos;s Mind
                            </>
                          )}
                        </button>
                        {expandedReasoning.has(index) && (
                          <div className="mt-2 p-3 bg-purple-50 dark:bg-purple-950/30 rounded-lg border border-purple-200 dark:border-purple-800 text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap max-h-60 overflow-y-auto">
                            {message.reasoning}
                          </div>
                        )}
                      </div>
                    )}
                    
                    <p className={`text-xs mt-1 ${message.role === 'user' ? 'text-green-100' : 'text-gray-500'}`}>
                      {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}
              
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl px-4 py-2">
                    <div className="flex items-center gap-2">
                      <Bot className="h-4 w-4 text-green-600" />
                      <Loader2 className="h-4 w-4 animate-spin text-green-600" />
                      <span className="text-sm text-gray-500">Flora is thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </CardContent>

            <CardFooter className="bg-white dark:bg-gray-950 border-t p-3">
              <div className="w-full space-y-2">
                {/* Image Preview */}
                {imagePreview && (
                  <div className="relative inline-block">
                    <img src={imagePreview} alt="Upload preview" className="h-16 w-16 object-cover rounded-lg border border-green-300" />
                    <button
                      onClick={clearImage}
                      className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full p-0.5 hover:bg-red-600 transition-colors"
                    >
                      <XCircle className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}
                {/* Input Row */}
                <div className="flex gap-2 w-full items-center">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleImageSelect}
                    className="hidden"
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={loading}
                    className="text-green-600 hover:bg-green-50 dark:hover:bg-green-950 flex-shrink-0"
                    title="Upload crop image"
                  >
                    <ImagePlus className="h-5 w-5" />
                  </Button>
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={selectedImage ? "Describe the issue..." : "Ask Flora anything..."}
                    disabled={loading}
                    className="flex-1"
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={loading || (!input.trim() && !selectedImage)}
                    size="icon"
                    className="bg-green-600 hover:bg-green-700 flex-shrink-0"
                  >
                    {loading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </CardFooter>
          </Card>
        </div>
      )}
    </>
  )
}
