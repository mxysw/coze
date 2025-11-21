// Bot ID is injected by backend from .env (COZE_BOT_ID)
const BOT_ID = window.COZE_BOT_ID || '7574314241218904100';
const TOKEN_ENDPOINT = window.COZE_TOKEN_ENDPOINT || '/api/chat-token';
const LOCAL_UID_KEY = 'coze-demo-uid';

const cozeUserId = (() => {
  const cached = localStorage.getItem(LOCAL_UID_KEY);
  if (cached) {
    return cached;
  }
  const generated = `user_${crypto.randomUUID()}`;
  localStorage.setItem(LOCAL_UID_KEY, generated);
  return generated;
})();

async function fetchChatToken(userId) {
  const response = await fetch(TOKEN_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId }),
  });

  if (!response.ok) {
    const info = await response.json().catch(() => ({}));
    throw new Error(info.error || `Failed to fetch token (${response.status})`);
  }
  return response.json();
}

async function bootstrapChat() {
  const { token } = await fetchChatToken(cozeUserId);
  
  if (!token) {
    throw new Error('Failed to obtain token from backend');
  }
  
  console.log('[DEBUG] Got token:', token.substring(0, 20) + '...');

  return new CozeWebSDK.WebChatClient({
    config: {
      type: 'bot',
      bot_id: BOT_ID,
      isIframe: false,
    },
    auth: {
      type: 'token',
      token,
      onRefreshToken: async () => {
        console.log('[DEBUG] Refreshing token...');
        const { token: newToken } = await fetchChatToken(cozeUserId);
        return newToken;
      },
    },
    userInfo: {
      id: cozeUserId,
      url: 'https://lf-coze-web-cdn.coze.cn/obj/eden-cn/lm-lgvj/ljhwZthlaukjlkulzlp/coze/coze-logo.png',
      nickname: cozeUserId,
    },
    ui: {
      base: {
        icon: 'https://lf-coze-web-cdn.coze.cn/obj/eden-cn/lm-lgvj/ljhwZthlaukjlkulzlp/coze/chatsdk-logo.png',
        layout: 'pc',
        lang: 'en',
        zIndex: 1000,
      },
      header: {
        isShow: true,
        isNeedClose: true,
      },
      asstBtn: {
        isNeed: true,
      },
      footer: {
        isShow: true,
        expressionText: 'Powered by ...',
      },
      chatBot: {
        title: 'Coze Bot',
        uploadable: true,
        width: 390,
      },
    },
  });
}

bootstrapChat().catch((error) => {
  console.error('Failed to initialize chat client', error);
  alert('Chat client failed to start, please try again later.');
});