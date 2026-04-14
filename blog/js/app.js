class BlogApp {
    constructor() {
        this.posts = [];
        this.currentPage = 1;
        this.postsPerPage = 10;
        this.filteredPosts = [];
        this.currentView = 'list';
        this.init();
    }

    async init() {
        await this.loadPosts();
        this.setupEventListeners();
        this.renderCategories();
        this.renderTags();
        this.renderRecentPosts();
        this.renderPosts();
        this.handleHashChange();
    }

    async loadPosts() {
        try {
            const response = await fetch('data/posts.json');
            this.posts = await response.json();
            this.filteredPosts = [...this.posts];
        } catch (error) {
            console.error('Failed to load posts:', error);
        }
    }

    setupEventListeners() {
        window.addEventListener('hashchange', () => this.handleHashChange());
        
        document.getElementById('searchBtn').addEventListener('click', () => this.search());
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.search();
        });
        
        document.getElementById('backBtn').addEventListener('click', () => {
            this.showListView();
            window.location.hash = '/';
        });

        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            });
        });
    }

    handleHashChange() {
        const hash = window.location.hash;
        
        if (hash.startsWith('#/post/')) {
            const slug = hash.replace('#/post/', '');
            this.showArticleDetail(slug);
        } else if (hash.startsWith('#/category/')) {
            const category = decodeURIComponent(hash.replace('#/category/', ''));
            this.filterByCategory(category);
        } else if (hash.startsWith('#/tag/')) {
            const tag = decodeURIComponent(hash.replace('#/tag/', ''));
            this.filterByTag(tag);
        } else {
            this.showListView();
        }
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const options = {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return date.toLocaleDateString('zh-CN', options);
    }

    renderCategories() {
        const categories = {};
        this.posts.forEach(post => {
            categories[post.category] = (categories[post.category] || 0) + 1;
        });

        const categoryList = document.getElementById('categoryList');
        categoryList.innerHTML = Object.entries(categories)
            .sort((a, b) => b[1] - a[1])
            .map(([category, count]) => `
                <li>
                    <a href="#/category/${encodeURIComponent(category)}" 
                       onclick="blogApp.filterByCategory('${category}'); return false;">
                        ${category} (${count})
                    </a>
                </li>
            `).join('');
    }

    renderTags() {
        const tags = {};
        this.posts.forEach(post => {
            post.tags.forEach(tag => {
                tags[tag] = (tags[tag] || 0) + 1;
            });
        });

        const tagList = document.getElementById('tagList');
        tagList.innerHTML = Object.entries(tags)
            .sort((a, b) => b[1] - a[1])
            .map(([tag, count]) => `
                <a href="#/tag/${encodeURIComponent(tag)}" 
                   class="tag"
                   onclick="blogApp.filterByTag('${tag}'); return false;">
                    ${tag}
                </a>
            `).join('');
    }

    renderRecentPosts() {
        const recentPosts = this.posts.slice(0, 5);
        const recentPostsList = document.getElementById('recentPosts');
        recentPostsList.innerHTML = recentPosts.map(post => `
            <li>
                <a href="#/post/${post.slug}" 
                   onclick="blogApp.showArticleDetail('${post.slug}'); return false;">
                    ${post.title}
                </a>
            </li>
        `).join('');
    }

    renderPosts() {
        const start = (this.currentPage - 1) * this.postsPerPage;
        const end = start + this.postsPerPage;
        const postsToShow = this.filteredPosts.slice(start, end);

        const articleList = document.getElementById('articleList');
        articleList.innerHTML = postsToShow.map(post => `
            <article class="article-card">
                <div class="article-meta">
                    <span class="article-date">📅 ${this.formatDate(post.date)}</span>
                    <span class="article-category">📁 ${post.category}</span>
                </div>
                <h2 class="article-title">
                    <a href="#/post/${post.slug}" 
                       onclick="blogApp.showArticleDetail('${post.slug}'); return false;">
                        ${post.title}
                    </a>
                </h2>
                <p class="article-excerpt">${post.excerpt}</p>
                <div class="article-tags">
                    ${post.tags.map(tag => `
                        <a href="#/tag/${encodeURIComponent(tag)}" 
                           class="article-tag"
                           onclick="blogApp.filterByTag('${tag}'); return false;">
                            #${tag}
                        </a>
                    `).join('')}
                </div>
            </article>
        `).join('');

        this.renderPagination();
    }

    renderPagination() {
        const totalPages = Math.ceil(this.filteredPosts.length / this.postsPerPage);
        const pagination = document.getElementById('pagination');
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        let paginationHTML = '';
        
        paginationHTML += `
            <button class="pagination-btn" 
                    onclick="blogApp.goToPage(${this.currentPage - 1})"
                    ${this.currentPage === 1 ? 'disabled' : ''}>
                上一页
            </button>
        `;

        for (let i = 1; i <= totalPages; i++) {
            paginationHTML += `
                <button class="pagination-btn ${i === this.currentPage ? 'active' : ''}"
                        onclick="blogApp.goToPage(${i})">
                    ${i}
                </button>
            `;
        }

        paginationHTML += `
            <button class="pagination-btn"
                    onclick="blogApp.goToPage(${this.currentPage + 1})"
                    ${this.currentPage === totalPages ? 'disabled' : ''}>
                下一页
            </button>
        `;

        pagination.innerHTML = paginationHTML;
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredPosts.length / this.postsPerPage);
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.renderPosts();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    search() {
        const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
        
        if (!searchTerm) {
            this.filteredPosts = [...this.posts];
        } else {
            this.filteredPosts = this.posts.filter(post => 
                post.title.toLowerCase().includes(searchTerm) ||
                post.content.toLowerCase().includes(searchTerm) ||
                post.excerpt.toLowerCase().includes(searchTerm)
            );
        }

        this.currentPage = 1;
        this.showListView();
        this.renderPosts();
    }

    filterByCategory(category) {
        this.filteredPosts = this.posts.filter(post => post.category === category);
        this.currentPage = 1;
        this.showListView();
        this.renderPosts();
    }

    filterByTag(tag) {
        this.filteredPosts = this.posts.filter(post => post.tags.includes(tag));
        this.currentPage = 1;
        this.showListView();
        this.renderPosts();
    }

    showListView() {
        this.currentView = 'list';
        document.querySelector('.main').classList.remove('hidden');
        document.getElementById('articleDetail').classList.add('hidden');
    }

    showArticleDetail(slug) {
        const post = this.posts.find(p => p.slug === slug);
        if (!post) return;

        this.currentView = 'detail';
        document.querySelector('.main').classList.add('hidden');
        document.getElementById('articleDetail').classList.remove('hidden');

        const articleContent = document.getElementById('articleContent');
        articleContent.innerHTML = `
            <h1>${post.title}</h1>
            <div class="article-meta">
                <span class="article-date">📅 ${this.formatDate(post.date)}</span>
                <span class="article-category">📁 ${post.category}</span>
            </div>
            <div class="article-tags" style="margin-bottom: 30px;">
                ${post.tags.map(tag => `<span class="article-tag">#${tag}</span>`).join('')}
            </div>
            <div class="markdown-body">
                ${this.renderMarkdown(post.content)}
            </div>
        `;

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    renderMarkdown(content) {
        if (typeof marked !== 'undefined') {
            return marked.parse(content);
        }
        return this.simpleMarkdown(content);
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
}

const blogApp = new BlogApp();
