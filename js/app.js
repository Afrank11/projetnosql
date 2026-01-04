const API_BASE_URL = 'http://localhost:5000/api';

const state = {
  currentUser: JSON.parse(localStorage.getItem('currentUser')),
  isAuthenticated: !!localStorage.getItem('currentUser'),
};

const api = {
  // LOGIN: Connects UI to MongoDB & Redis
  async login(email, password) {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!response.ok) throw new Error('User not found');
    const user = await response.json();
    localStorage.setItem('currentUser', JSON.stringify(user));
    window.location.href = 'index.html';
  },

  // CREATE POST: Saves data to MongoDB
  async createPost(content) {
    const response = await fetch(`${API_BASE_URL}/posts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        author_id: state.currentUser.username, 
        content: content,
        created_at: new Date()
      })
    });
    return await response.json();
  },

  async getPosts() {
    const response = await fetch(`${API_BASE_URL}/posts`);
    return await response.json();
  },

  logout() {
    localStorage.removeItem('currentUser');
    window.location.href = 'login.html';
  }
};

// HANDLER: Connects the "Post" button to the API
async function handleCreatePost() {
    const content = document.getElementById('post-content').value;
    if (!content) return alert("Write something first!");
    
    await api.createPost(content);
    alert("Post saved to MongoDB!");
    window.location.href = 'index.html';
}

// INITIALIZER: Runs when page loads
window.onload = async () => {
    const path = window.location.pathname;
    
    if (path.includes('index.html') || path === '/') {
        const posts = await api.getPosts();
        const container = document.getElementById('posts-container');
        container.innerHTML = posts.map(p => `
            <div class="post-card">
                <strong>@${p.author_id}</strong>
                <p>${p.content}</p>
                <div class="post-actions">❤️ Like</div>
            </div>
        `).join('');
    }
};
