import { useState, useRef, useEffect } from 'react';
import { aiApi } from '@/api/client';
import { Send, Bot, User, Sparkles } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  pipeline?: string;
}

export default function AIChatPage() {
  const [messages, setMessages] = useState<Message[]>([{
    role: 'assistant',
    content: '您好！我是 OmicsFlow AI 助手。请描述您的数据类型和分析需求，我会为您推荐最合适的分析管线。\n\n支持的分析类型：\n• RNA-seq 基因表达\n• WGS 变异检测\n• 16S/ITS 扩增子\n• TCR/BCR 免疫组库\n• ATAC-seq 染色质可及性\n• 空间转录组\n• ChIP-seq / small RNA / 甲基化 / 长读长 / WES / 蛋白质组',
  }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => Math.random().toString(36).substring(2, 10));
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);
    try {
      const res = await aiApi.chat(userMessage, sessionId);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.data.message,
        pipeline: res.data.pipeline,
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '抱歉，处理请求时出错。请重试。',
      }]);
    } finally {
      setLoading(false);
    }
  };

  const renderContent = (content: string) => {
    return content.split('\n').map((line, i) => {
      if (line.startsWith('```')) return null;
      if (line.startsWith('**')) {
        return <p key={i} className="font-semibold mt-2">{line.replace(/\*\*/g, '')}</p>;
      }
      if (line.startsWith('- ') || line.startsWith('• ')) {
        return <p key={i} className="ml-4 text-sm">{line}</p>;
      }
      if (line.match(/^\d+\./)) {
        return <p key={i} className="ml-4 text-sm">{line}</p>;
      }
      return <p key={i}>{line || <br />}</p>;
    });
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles size={24} className="text-purple-600" />
        <h1 className="text-2xl font-bold">AI 分析助手</h1>
        <span className="text-sm text-gray-500 ml-2">描述您的数据，AI 推荐最佳管线</span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 p-4 bg-white rounded-lg border">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                <Bot size={18} className="text-purple-600" />
              </div>
            )}
            <div className={`max-w-[75%] rounded-xl px-4 py-3 ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-800'
            }`}>
              <div className="text-sm leading-relaxed whitespace-pre-wrap">
                {renderContent(msg.content)}
              </div>
              {msg.pipeline && (
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
                    推荐管线: {msg.pipeline}
                  </span>
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                <User size={18} className="text-blue-600" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
              <Bot size={18} className="text-purple-600 animate-pulse" />
            </div>
            <div className="bg-gray-100 rounded-xl px-4 py-3">
              <span className="text-sm text-gray-500 animate-pulse">思考中...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="mt-4 flex gap-2">
        <input
          type="text"
          className="flex-1 px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
          placeholder="描述您的数据和分析需求，如：我有一批 RNA-seq 数据，想比较两组的差异表达..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          disabled={loading}
        />
        <button
          onClick={handleSend}
          className="px-6 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors disabled:opacity-50"
          disabled={loading || !input.trim()}
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  );
}