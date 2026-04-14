class BlogMinimal {
    constructor() {
        this.posts = [];
        this.currentPage = 1;
        this.pageSize = 9;
        this.currentCategory = '';
        this.viewingPost = null;
        this.init();
    }

    async init() {
        await this.loadPosts();
        this.setupEventListeners();
        this.setupRoutes();
        this.render();
    }

    async loadPosts() {
        try {
            const response = await fetch('data/posts.json');
            this.posts = await response.json();
        } catch (error) {
            console.error('加载文章失败:', error);
        }
    }

    setupRoutes() {
        const hash = window.location.hash;
        if (hash.startsWith('#/post/')) {
            const postId = parseInt(hash.replace('#/post/', ''));
            this.viewingPost = this.posts.find(p => p.id === postId);
        } else {
            this.viewingPost = null;
            this.currentPage = 1;
        }
        this.render();
    }

    setupEventListeners() {
        window.addEventListener('hashchange', () => this.setupRoutes());
    }

    render() {
        const listView = document.getElementById('list-view');
        const postView = document.getElementById('post-view');
        
        if (this.viewingPost) {
            listView.style.display = 'none';
            postView.style.display = 'block';
            this.renderArticleDetail();
        } else {
            listView.style.display = 'block';
            postView.style.display = 'none';
            this.renderCategoryFilters();
            this.renderArticleGrid();
            this.renderPagination();
            this.renderSidebar();
        }
    }

    viewList() {
        window.location.hash = '#/';
    }

    viewPost(postId) {
        window.location.hash = `#/post/${postId}`;
    }

    renderCategoryFilters() {
        const container = document.getElementById('category-filters');
        if (!container) return;

        const categories = new Set();
        this.posts.forEach(post => {
            if (post.category) {
                categories.add(post.category);
            }
        });

        let html = `<button class="filter-btn ${!this.currentCategory ? 'active' : ''}" onclick="blog.setCategory('')">全部</button>`;
        
        Array.from(categories).sort().forEach(category => {
            html += `<button class="filter-btn ${this.currentCategory === category ? 'active' : ''}" onclick="blog.setCategory('${category}')">${this.escapeHtml(category)}</button>`;
        });

        container.innerHTML = html;
    }

    setCategory(category) {
        this.currentCategory = category;
        this.currentPage = 1;
        this.render();
    }

    renderArticleGrid() {
        const container = document.getElementById('articles-grid');
        if (!container) return;

        let filteredPosts = this.posts;
        
        if (this.currentCategory) {
            filteredPosts = this.posts.filter(post => post.category === this.currentCategory);
        }

        const start = (this.currentPage - 1) * this.pageSize;
        const end = start + this.pageSize;
        const pagePosts = filteredPosts.slice(start, end);

        if (pagePosts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>暂无文章</h3>
                    <p>还没有文章，快来添加第一篇吧！</p>
                </div>
            `;
            return;
        }

        container.innerHTML = pagePosts.map(post => `
            <article class="article-card" onclick="blog.viewPost(${post.id})">
                <div class="article-meta">
                    ${post.category ? `<span class="article-category">${this.escapeHtml(post.category)}</span>` : ''}
                    <span>${this.formatDate(post.date)}</span>
                </div>
                <h3>${this.escapeHtml(post.title)}</h3>
                <p class="excerpt">${this.escapeHtml(post.excerpt || post.content.slice(0, 150) + '...')}</p>
                ${post.tags && post.tags.length > 0 ? `
                    <div class="article-tags">
                        ${post.tags.slice(0, 3).map(tag => `<span class="tag">${this.escapeHtml(tag)}</span>`).join('')}
                    </div>
                ` : ''}
            </article>
        `).join('');
    }

    renderPagination() {
        const container = document.getElementById('pagination');
        if (!container) return;

        let filteredPosts = this.posts;
        if (this.currentCategory) {
            filteredPosts = this.posts.filter(post => post.category === this.currentCategory);
        }

        const totalPages = Math.ceil(filteredPosts.length / this.pageSize);
        
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let html = '';
        
        html += `<button onclick="blog.goToPage(${this.currentPage - 1})" ${this.currentPage === 1 ? 'disabled' : ''}>
            ← 上一页
        </button>`;

        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || 
                (i >= this.currentPage - 2 && i <= this.currentPage + 2)) {
                html += `<button onclick="blog.goToPage(${i})" class="${i === this.currentPage ? 'active' : ''}">${i}</button>`;
            } else if (i === this.currentPage - 3 || i === this.currentPage + 3) {
                html += `<span>...</span>`;
            }
        }

        html += `<button onclick="blog.goToPage(${this.currentPage + 1})" ${this.currentPage === totalPages ? 'disabled' : ''}>
            下一页 →
        </button>`;

        container.innerHTML = html;
    }

    goToPage(page) {
        let filteredPosts = this.posts;
        if (this.currentCategory) {
            filteredPosts = this.posts.filter(post => post.category === this.currentCategory);
        }
        
        const totalPages = Math.ceil(filteredPosts.length / this.pageSize);
        
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.renderArticleGrid();
            this.renderPagination();
        }
    }

    renderSidebar() {
        this.renderRecentArticles();
        this.renderSidebarCategories();
        this.renderSidebarTags();
    }

    renderRecentArticles() {
        const container = document.getElementById('recent-articles');
        if (!container) return;

        const recentPosts = this.posts.slice(0, 5);
        container.innerHTML = recentPosts.map(post => `
            <li><a href="#/post/${post.id}" onclick="blog.viewPost(${post.id}); return false;">${this.escapeHtml(post.title)}</a></li>
        `).join('');
    }

    renderSidebarCategories() {
        const container = document.getElementById('sidebar-categories');
        if (!container) return;

        const categoryCounts = {};
        this.posts.forEach(post => {
            if (post.category) {
                categoryCounts[post.category] = (categoryCounts[post.category] || 0) + 1;
            }
        });

        container.innerHTML = Object.entries(categoryCounts)
            .sort((a, b) => b[1] - a[1])
            .map(([category, count]) => `
                <li><a href="#" onclick="blog.setCategory('${category}'); return false;">${this.escapeHtml(category)} (${count})</a></li>
            `).join('');
    }

    renderSidebarTags() {
        const container = document.getElementById('sidebar-tags');
        if (!container) return;

        const tagCounts = {};
        this.posts.forEach(post => {
            if (post.tags) {
                post.tags.forEach(tag => {
                    tagCounts[tag] = (tagCounts[tag] || 0) + 1;
                });
            }
        });

        container.innerHTML = Object.entries(tagCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 15)
            .map(([tag, count]) => `<span class="tag">${this.escapeHtml(tag)}</span>`)
            .join('');
    }

    renderArticleDetail() {
        const postView = document.getElementById('post-view');
        if (!postView || !this.viewingPost) return;

        postView.innerHTML = `
            <a href="#/" class="back-btn" onclick="blog.viewList(); return false;">
                ← 返回列表
            </a>
            
            <article class="article-detail">
                <div class="article-detail-header">
                    <h1>${this.escapeHtml(this.viewingPost.title)}</h1>
                    <div class="article-detail-meta">
                        ${this.viewingPost.category ? `<span>分类：${this.escapeHtml(this.viewingPost.category)}</span>` : ''}
                        <span>${this.formatDate(this.viewingPost.date)}</span>
                    </div>
                </div>
                <div class="article-content">
                    ${this.simpleMarkdown(this.viewingPost.content)}
                </div>
                ${this.viewingPost.tags && this.viewingPost.tags.length > 0 ? `
                    <div class="article-tags" style="margin-top: 40px; padding-top: 24px; border-top: 1px solid var(--border-color);">
                        ${this.viewingPost.tags.map(tag => `<span class="tag">${this.escapeHtml(tag)}</span>`).join('')}
                    </div>
                ` : ''}
            </article>
        `;
    }

    simpleMarkdown(content) {
        return content
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/\*\*(.*)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*)\*/g, '<em>$1</em>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/^- (.*$)/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/^(?!<[hul])(.*)$/gm, '<p>$1</p>');
    }

    formatDate(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        
        return `${year}-${month}-${day}`;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

let blog;
document.addEventListener('DOMContentLoaded', () => {
    blog = new BlogMinimal();
});
