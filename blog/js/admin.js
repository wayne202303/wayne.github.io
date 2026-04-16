class BlogAdmin {
    constructor() {
        this.posts = [];
        this.tags = [];
        this.categories = [];
        this.selectedTags = [];
        this.currentPost = null;
        this.editingPostId = null;
        this.currentPage = 1;
        this.pageSize = 10;
        this.filteredPosts = [];
        this.selectedPostIds = new Set();
        this.deletingPostId = null;
        this.deletingCategoryName = null;
        this.editingTagName = null;
        this.importData = [];
        
        // 评论相关属性
        this.allComments = [];
        this.filteredComments = [];
        this.currentCommentPage = 1;
        this.commentPageSize = 10;
        this.selectedCommentIds = new Set();
        this.editingComment = null;
        
        this.init();
    }
    
    async init() {
        await this.loadPosts();
        this.setupEventListeners();
        this.renderStats();
        this.render();
    }
    
    async loadPosts() {
        try {
            const response = await fetch('data/posts.json');
            this.posts = await response.json();
            this.filteredPosts = [...this.posts];
            this.processMetadata();
        } catch (error) {
            this.showToast('加载数据失败', 'error');
            console.error(error);
        }
    }
    
    processMetadata() {
        const categories = new Set();
        const tags = new Map();
        
        this.posts.forEach(post => {
            if (post.category) {
                categories.add(post.category);
            }
            
            if (post.tags) {
                post.tags.forEach(tag => {
                    const count = tags.get(tag) || 0;
                    tags.set(tag, count + 1);
                });
            }
        });
        
        this.categories = Array.from(categories).sort();
        this.tags = Array.from(tags.entries()).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count);
        
        // 处理评论数据
        this.allComments = [];
        this.posts.forEach(post => {
            if (post.comments) {
                post.comments.forEach(comment => {
                    this.allComments.push({
                        ...comment,
                        postId: post.id,
                        postTitle: post.title
                    });
                });
            }
        });
        // 按时间倒序排列评论
        this.allComments.sort((a, b) => new Date(b.date) - new Date(a.date));
        this.filteredComments = [...this.allComments];
    }
    
    setupEventListeners() {
        // 退出登录
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }
        
        document.querySelectorAll('.admin-menu li').forEach(item => {
            item.addEventListener('click', () => this.switchTab(item.dataset.tab));
        });
        
        document.getElementById('add-article-btn').addEventListener('click', () => this.openArticleModal());
        document.getElementById('save-article-btn').addEventListener('click', () => this.saveArticle());
        document.getElementById('new-category-btn').addEventListener('click', () => this.createNewCategory());
        
        document.getElementById('batch-delete-btn').addEventListener('click', () => this.batchDelete());
        document.getElementById('select-all').addEventListener('change', (e) => this.toggleSelectAll(e.target.checked));
        
        document.getElementById('add-tag-btn').addEventListener('click', () => this.openTagModal());
        document.getElementById('save-tag-btn').addEventListener('click', () => this.saveTag());
        document.getElementById('save-category-btn').addEventListener('click', () => this.saveCategory());
        document.getElementById('delete-category-btn').addEventListener('click', () => this.deleteCategory());
        document.getElementById('confirm-delete-category-btn').addEventListener('click', () => this.confirmDeleteCategory());
        
        document.getElementById('import-btn').addEventListener('click', () => this.openImportModal());
        document.getElementById('confirm-import-btn').addEventListener('click', () => this.confirmImport());
        document.getElementById('import-file').addEventListener('change', (e) => this.previewImport(e));
        
        document.getElementById('search-input').addEventListener('input', () => this.applyFilters());
        document.getElementById('year-filter').addEventListener('change', () => this.applyFilters());
        document.getElementById('category-filter').addEventListener('change', () => this.applyFilters());
        document.getElementById('tag-filter').addEventListener('change', () => this.applyFilters());
        
        document.getElementById('tag-search').addEventListener('input', (e) => this.searchTags(e.target.value));
        document.getElementById('tag-search').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.addTagFromInput();
            }
        });
        
        document.querySelectorAll('.modal-close, .modal-cancel').forEach(btn => {
            btn.addEventListener('click', () => this.closeModals());
        });
        
        document.getElementById('confirm-delete-btn').addEventListener('click', () => this.confirmDelete());
        
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModals();
                }
            });
        });
        
        // 评论相关事件监听器
        document.getElementById('save-comment-btn').addEventListener('click', () => this.saveComment());
        document.getElementById('batch-delete-comments-btn').addEventListener('click', () => this.batchDeleteComments());
        document.getElementById('select-all-comments').addEventListener('change', (e) => this.toggleSelectAllComments(e.target.checked));
        document.getElementById('comment-search-input').addEventListener('input', () => this.applyCommentFilters());
        document.getElementById('comment-article-filter').addEventListener('change', () => this.applyCommentFilters());
    }
    
    switchTab(tabName) {
        document.querySelectorAll('.admin-menu li').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        if (tabName === 'articles') {
            this.render();
        } else if (tabName === 'comments') {
            this.renderComments();
        } else if (tabName === 'tags') {
            this.renderTags();
        } else if (tabName === 'stats') {
            this.renderStats();
        }
    }
    
    render() {
        this.renderFilters();
        this.renderTable();
        this.renderPagination();
    }
    
    renderFilters() {
        const years = new Set();
        this.posts.forEach(post => {
            if (post.date) {
                const year = new Date(post.date).getFullYear();
                years.add(year);
            }
        });
        
        const yearFilter = document.getElementById('year-filter');
        yearFilter.innerHTML = '<option value="">全部年份</option>';
        Array.from(years).sort((a, b) => b - a).forEach(year => {
            yearFilter.innerHTML += `<option value="${year}">${year}年</option>`;
        });
        
        const categoryFilter = document.getElementById('category-filter');
        categoryFilter.innerHTML = '<option value="">全部分类</option>';
        this.categories.forEach(category => {
            categoryFilter.innerHTML += `<option value="${category}">${category}</option>`;
        });
        
        const tagFilter = document.getElementById('tag-filter');
        tagFilter.innerHTML = '<option value="">全部标签</option>';
        this.tags.forEach(tag => {
            tagFilter.innerHTML += `<option value="${tag.name}">${tag.name}</option>`;
        });
    }
    
    applyFilters() {
        const searchTerm = document.getElementById('search-input').value.toLowerCase();
        const yearFilter = document.getElementById('year-filter').value;
        const categoryFilter = document.getElementById('category-filter').value;
        const tagFilter = document.getElementById('tag-filter').value;
        
        this.filteredPosts = this.posts.filter(post => {
            if (searchTerm) {
                const searchIn = (post.title + ' ' + post.content + ' ' + (post.excerpt || '')).toLowerCase();
                if (!searchIn.includes(searchTerm)) return false;
            }
            
            if (yearFilter) {
                const year = new Date(post.date).getFullYear();
                if (year !== parseInt(yearFilter)) return false;
            }
            
            if (categoryFilter && post.category !== categoryFilter) return false;
            
            if (tagFilter && (!post.tags || !post.tags.includes(tagFilter))) return false;
            
            return true;
        });
        
        this.currentPage = 1;
        this.renderTable();
        this.renderPagination();
    }
    
    renderTable() {
        const tbody = document.getElementById('articles-table-body');
        const start = (this.currentPage - 1) * this.pageSize;
        const end = start + this.pageSize;
        const pagePosts = this.filteredPosts.slice(start, end);
        
        tbody.innerHTML = pagePosts.map(post => `
            <tr>
                <td>
                    <input type="checkbox" class="post-checkbox" data-id="${post.id}" 
                        ${this.selectedPostIds.has(post.id) ? 'checked' : ''}>
                </td>
                <td>${post.id}</td>
                <td>
                    <strong>${this.escapeHtml(post.title)}</strong>
                </td>
                <td>${this.escapeHtml(post.category || '-')}</td>
                <td>
                    <div class="tags">
                        ${(post.tags || []).slice(0, 3).map(tag => 
                            `<span class="tag">${this.escapeHtml(tag)}</span>`
                        ).join('')}
                        ${(post.tags || []).length > 3 ? 
                            `<span class="tag">+${post.tags.length - 3}</span>` : ''}
                    </div>
                </td>
                <td>${this.formatDate(post.date)}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn view" onclick="admin.viewArticle(${post.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="action-btn edit" onclick="admin.openArticleModal(${post.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-btn delete" onclick="admin.openDeleteModal(${post.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
        
        document.querySelectorAll('.post-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const id = parseInt(e.target.dataset.id);
                if (e.target.checked) {
                    this.selectedPostIds.add(id);
                } else {
                    this.selectedPostIds.delete(id);
                }
            });
        });
    }
    
    renderPagination() {
        const totalPages = Math.ceil(this.filteredPosts.length / this.pageSize);
        const pagination = document.getElementById('admin-pagination');
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }
        
        let html = '';
        
        html += `<button onclick="admin.goToPage(${this.currentPage - 1})" 
            ${this.currentPage === 1 ? 'disabled' : ''}>
            <i class="fas fa-chevron-left"></i> 上一页
        </button>`;
        
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || 
                (i >= this.currentPage - 2 && i <= this.currentPage + 2)) {
                html += `<button onclick="admin.goToPage(${i})" 
                    class="${i === this.currentPage ? 'active' : ''}">${i}</button>`;
            } else if (i === this.currentPage - 3 || i === this.currentPage + 3) {
                html += `<span>...</span>`;
            }
        }
        
        html += `<button onclick="admin.goToPage(${this.currentPage + 1})" 
            ${this.currentPage === totalPages ? 'disabled' : ''}>
            下一页 <i class="fas fa-chevron-right"></i>
        </button>`;
        
        pagination.innerHTML = html;
    }
    
    goToPage(page) {
        const totalPages = Math.ceil(this.filteredPosts.length / this.pageSize);
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.renderTable();
            this.renderPagination();
        }
    }
    
    toggleSelectAll(checked) {
        const start = (this.currentPage - 1) * this.pageSize;
        const end = start + this.pageSize;
        const pagePosts = this.filteredPosts.slice(start, end);
        
        pagePosts.forEach(post => {
            if (checked) {
                this.selectedPostIds.add(post.id);
            } else {
                this.selectedPostIds.delete(post.id);
            }
        });
        
        this.renderTable();
    }
    
    openArticleModal(postId = null) {
        this.editingPostId = postId;
        this.selectedTags = [];
        
        const modal = document.getElementById('article-modal');
        const title = document.getElementById('modal-title');
        
        if (postId) {
            const post = this.posts.find(p => p.id === postId);
            if (post) {
                title.textContent = '编辑文章';
                document.getElementById('article-id').value = post.id;
                document.getElementById('article-title').value = post.title;
                document.getElementById('article-slug').value = post.slug || '';
                document.getElementById('article-excerpt').value = post.excerpt || '';
                document.getElementById('article-content').value = post.content || '';
                document.getElementById('article-category').value = post.category || '';
                
                if (post.date) {
                    const date = new Date(post.date);
                    document.getElementById('article-date').value = 
                        date.toISOString().slice(0, 16);
                }
                
                this.selectedTags = [...(post.tags || [])];
            }
        } else {
            title.textContent = '新增文章';
            document.getElementById('article-form').reset();
            document.getElementById('article-date').value = 
                new Date().toISOString().slice(0, 16);
        }
        
        this.updateCategoryDropdown();
        this.renderSelectedTags();
        modal.classList.add('active');
    }
    
    updateCategoryDropdown() {
        const select = document.getElementById('article-category');
        const currentValue = select.value;
        
        select.innerHTML = '<option value="">请选择分类</option>';
        this.categories.forEach(category => {
            select.innerHTML += `<option value="${category}">${category}</option>`;
        });
        
        select.value = currentValue;
    }
    
    createNewCategory() {
        const modal = document.getElementById('category-modal');
        document.getElementById('category-name').value = '';
        modal.classList.add('active');
    }

    saveCategory() {
        const name = document.getElementById('category-name').value.trim();
        if (name) {
            if (!this.categories.includes(name)) {
                this.categories.push(name);
                this.categories.sort();
                this.updateAllCategoryDropdowns();
                document.getElementById('article-category').value = name;
                
                // 保存数据到服务器
                this.savePosts();
                
                this.showToast('分类创建成功', 'success');
                this.closeModals();
            } else {
                this.showToast('分类已存在', 'error');
            }
        } else {
            this.showToast('请输入分类名称', 'error');
        }
    }

    deleteCategory() {
        const categorySelect = document.getElementById('article-category');
        const currentCategory = categorySelect.value;
        
        if (!currentCategory) {
            this.showToast('请先选择要删除的分类', 'error');
            return;
        }
        
        // 打开确认删除模态框
        document.getElementById('delete-category-message').textContent = 
            `确定要删除分类"${currentCategory}"吗？`;
        this.deletingCategoryName = currentCategory;
        document.getElementById('delete-category-modal').classList.add('active');
    }

    confirmDeleteCategory() {
        if (!this.deletingCategoryName) return;
        
        const categoryName = this.deletingCategoryName;
        
        // 从分类列表中移除
        const index = this.categories.indexOf(categoryName);
        if (index !== -1) {
            this.categories.splice(index, 1);
        }
        
        // 更新所有使用该分类的文章为"未分类"
        this.posts.forEach(post => {
            if (post.category === categoryName) {
                post.category = '未分类';
            }
        });
        
        // 更新所有下拉框
        this.updateAllCategoryDropdowns();
        
        // 清空当前选择
        document.getElementById('article-category').value = '';
        
        // 保存数据到服务器
        this.savePosts();
        
        this.showToast(`分类"${categoryName}"已删除`, 'success');
        this.closeModals();
        this.deletingCategoryName = null;
    }

    updateAllCategoryDropdowns() {
        // 更新文章编辑模态框的分类下拉框
        this.updateCategoryDropdown();
        
        // 更新筛选器的分类下拉框
        this.renderFilters();
        
        // 更新统计页面的分类统计
        this.renderStats();
    }
    
    searchTags(query) {
        const suggestions = document.getElementById('tag-suggestions');
        
        if (!query.trim()) {
            suggestions.classList.remove('active');
            return;
        }
        
        const matchingTags = this.tags
            .filter(tag => 
                tag.name.toLowerCase().includes(query.toLowerCase()) &&
                !this.selectedTags.includes(tag.name)
            )
            .slice(0, 5);
        
        if (matchingTags.length > 0) {
            suggestions.innerHTML = matchingTags.map(tag => 
                `<div class="tag-suggestion" onclick="admin.addTag('${tag.name}')">
                    ${this.escapeHtml(tag.name)}
                </div>`
            ).join('');
            suggestions.classList.add('active');
        } else {
            suggestions.innerHTML = 
                `<div class="tag-suggestion" onclick="admin.addTag('${query}')">
                    创建新标签: ${this.escapeHtml(query)}
                </div>`;
            suggestions.classList.add('active');
        }
    }
    
    addTagFromInput() {
        const input = document.getElementById('tag-search');
        const value = input.value.trim();
        if (value && !this.selectedTags.includes(value)) {
            this.addTag(value);
        }
        input.value = '';
    }
    
    addTag(tagName) {
        if (!this.selectedTags.includes(tagName)) {
            this.selectedTags.push(tagName);
            this.renderSelectedTags();
        }
        document.getElementById('tag-search').value = '';
        document.getElementById('tag-suggestions').classList.remove('active');
    }
    
    removeTag(tagName) {
        this.selectedTags = this.selectedTags.filter(t => t !== tagName);
        this.renderSelectedTags();
    }
    
    renderSelectedTags() {
        const container = document.getElementById('selected-tags');
        container.innerHTML = this.selectedTags.map(tag => 
            `<div class="selected-tag">
                ${this.escapeHtml(tag)}
                <span class="remove" onclick="admin.removeTag('${tag}')">&times;</span>
            </div>`
        ).join('');
    }
    
    saveArticle() {
        const title = document.getElementById('article-title').value.trim();
        const slug = document.getElementById('article-slug').value.trim() || 
            title.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9\-]/g, '');
        const category = document.getElementById('article-category').value;
        const excerpt = document.getElementById('article-excerpt').value.trim();
        const content = document.getElementById('article-content').value.trim();
        const dateValue = document.getElementById('article-date').value;
        
        if (!title || !content) {
            this.showToast('请填写必填字段', 'error');
            return;
        }
        
        if (this.editingPostId) {
            const index = this.posts.findIndex(p => p.id === this.editingPostId);
            if (index !== -1) {
                this.posts[index] = {
                    ...this.posts[index],
                    title,
                    slug,
                    category,
                    tags: [...this.selectedTags],
                    excerpt,
                    content,
                    date: dateValue ? new Date(dateValue).toISOString() : new Date().toISOString(),
                    updated_at: new Date().toISOString()
                };
            }
        } else {
            const newPost = {
                id: Math.max(...this.posts.map(p => p.id)) + 1,
                title,
                slug,
                category,
                tags: [...this.selectedTags],
                excerpt,
                content,
                date: dateValue ? new Date(dateValue).toISOString() : new Date().toISOString()
            };
            this.posts.unshift(newPost);
        }
        
        this.processMetadata();
        this.savePosts();
        this.closeModals();
        this.showToast(this.editingPostId ? '文章更新成功' : '文章创建成功', 'success');
    }
    
    viewArticle(postId) {
        window.open(`index.html?post=${postId}`, '_blank');
    }
    
    openDeleteModal(postId) {
        this.deletingPostId = postId;
        const modal = document.getElementById('delete-modal');
        document.getElementById('delete-message').textContent = '确定要删除这篇文章吗？';
        modal.classList.add('active');
    }
    
    confirmDelete() {
        if (this.deletingPostId !== null) {
            this.posts = this.posts.filter(p => p.id !== this.deletingPostId);
            this.processMetadata();
            this.savePosts();
            this.closeModals();
            this.showToast('文章删除成功', 'success');
        }
    }
    
    batchDelete() {
        if (this.selectedPostIds.size === 0) {
            this.showToast('请先选择要删除的文章', 'error');
            return;
        }
        
        const modal = document.getElementById('delete-modal');
        document.getElementById('delete-message').textContent = 
            `确定要删除选中的 ${this.selectedPostIds.size} 篇文章吗？`;
        modal.classList.add('active');
    }
    
    renderTags() {
        const tbody = document.getElementById('tags-table-body');
        tbody.innerHTML = this.tags.map(tag => `
            <tr>
                <td><strong>${this.escapeHtml(tag.name)}</strong></td>
                <td>${tag.count}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn edit" onclick="admin.openTagModal('${tag.name}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-btn delete" onclick="admin.deleteTag('${tag.name}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }
    
    openTagModal(tagName = null) {
        this.editingTagName = tagName;
        const modal = document.getElementById('tag-modal');
        const title = document.getElementById('tag-modal-title');
        
        if (tagName) {
            title.textContent = '编辑标签';
            document.getElementById('tag-old-name').value = tagName;
            document.getElementById('tag-name').value = tagName;
        } else {
            title.textContent = '新增标签';
            document.getElementById('tag-form').reset();
        }
        
        modal.classList.add('active');
    }
    
    saveTag() {
        const name = document.getElementById('tag-name').value.trim();
        const oldName = document.getElementById('tag-old-name').value;
        
        if (!name) {
            this.showToast('请输入标签名称', 'error');
            return;
        }
        
        if (this.editingTagName) {
            if (name !== oldName) {
                this.posts.forEach(post => {
                    if (post.tags) {
                        const index = post.tags.indexOf(oldName);
                        if (index !== -1) {
                            post.tags[index] = name;
                        }
                    }
                });
            }
        } else {
            if (this.tags.find(t => t.name === name)) {
                this.showToast('标签已存在', 'error');
                return;
            }
            
            // 新增标签时，将其添加到第一篇文章中，这样标签就会出现在标签列表中
            if (this.posts.length > 0) {
                const firstPost = this.posts[0];
                if (!firstPost.tags) {
                    firstPost.tags = [];
                }
                if (!firstPost.tags.includes(name)) {
                    firstPost.tags.push(name);
                }
            }
        }
        
        this.processMetadata();
        this.savePosts();
        this.closeModals();
        this.showToast(this.editingTagName ? '标签更新成功' : '标签创建成功', 'success');
        this.renderTags();
    }
    
    deleteTag(tagName) {
        if (confirm(`确定要删除标签 "${tagName}" 吗？`)) {
            this.posts.forEach(post => {
                if (post.tags) {
                    post.tags = post.tags.filter(t => t !== tagName);
                }
            });
            
            this.processMetadata();
            this.savePosts();
            this.renderTags();
            this.showToast('标签删除成功', 'success');
        }
    }
    
    openImportModal() {
        document.getElementById('import-modal').classList.add('active');
        document.getElementById('import-file').value = '';
        document.getElementById('import-preview').innerHTML = '';
        this.importData = [];
    }
    
    previewImport(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            const content = e.target.result;
            this.importData = this.parseImportContent(content);
            
            const preview = document.getElementById('import-preview');
            if (this.importData.length > 0) {
                preview.innerHTML = `
                    <h4>预览：${this.importData.length} 条记录</h4>
                    <ul>
                        ${this.importData.slice(0, 5).map(item => 
                            `<li>${this.escapeHtml(item.title)}</li>`
                        ).join('')}
                        ${this.importData.length > 5 ? 
                            `<li>... 还有 ${this.importData.length - 5} 条</li>` : ''}
                    </ul>
                `;
            } else {
                preview.innerHTML = '<p>未找到可导入的数据</p>';
            }
        };
        reader.readAsText(file, 'gbk');
    }
    
    parseImportContent(content) {
        const lines = content.split('\n').filter(line => line.trim());
        const data = [];
        
        for (let i = 1; i < lines.length; i++) {
            const parts = lines[i].split('\t');
            if (parts.length >= 3) {
                data.push({
                    time: parts[0].trim(),
                    title: parts[1].trim(),
                    content: parts.slice(2).join('\t').trim()
                });
            }
        }
        
        return data;
    }
    
    confirmImport() {
        if (this.importData.length === 0) {
            this.showToast('没有可导入的数据', 'error');
            return;
        }
        
        const currentMaxId = Math.max(...this.posts.map(p => p.id));
        let newId = currentMaxId + 1;
        
        this.importData.forEach(item => {
            const slug = item.title.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9\-]/g, '');
            
            let date;
            try {
                date = new Date(item.time).toISOString();
            } catch {
                date = new Date().toISOString();
            }
            
            this.posts.unshift({
                id: newId++,
                title: item.title,
                slug: slug + '-' + newId,
                category: '默认分类',
                tags: ['导入'],
                excerpt: item.content.slice(0, 100) + '...',
                content: item.content,
                date
            });
        });
        
        this.processMetadata();
        this.savePosts();
        this.closeModals();
        this.showToast(`成功导入 ${this.importData.length} 篇文章`, 'success');
    }
    
    renderStats() {
        document.getElementById('total-articles').textContent = this.posts.length;
        document.getElementById('total-categories').textContent = this.categories.length;
        document.getElementById('total-tags').textContent = this.tags.length;
        
        const yearlyStats = {};
        this.posts.forEach(post => {
            if (post.date) {
                const year = new Date(post.date).getFullYear();
                yearlyStats[year] = (yearlyStats[year] || 0) + 1;
            }
        });
        
        const yearlyContainer = document.getElementById('yearly-stats');
        const maxYearly = Math.max(...Object.values(yearlyStats), 1);
        yearlyContainer.innerHTML = Object.entries(yearlyStats)
            .sort((a, b) => b[0] - a[0])
            .map(([year, count]) => `
                <div class="stat-bar">
                    <span class="stat-bar-label">${year}年</span>
                    <div class="stat-bar-fill">
                        <div class="stat-bar-fill-inner" style="width: ${(count / maxYearly) * 100}%"></div>
                    </div>
                    <span class="stat-bar-count">${count}</span>
                </div>
            `).join('');
        
        const categoryStats = {};
        this.posts.forEach(post => {
            if (post.category) {
                categoryStats[post.category] = (categoryStats[post.category] || 0) + 1;
            }
        });
        
        const categoryContainer = document.getElementById('category-stats');
        const maxCategory = Math.max(...Object.values(categoryStats), 1);
        categoryContainer.innerHTML = Object.entries(categoryStats)
            .sort((a, b) => b[1] - a[1])
            .map(([category, count]) => `
                <div class="stat-bar">
                    <span class="stat-bar-label">${this.escapeHtml(category)}</span>
                    <div class="stat-bar-fill">
                        <div class="stat-bar-fill-inner" style="width: ${(count / maxCategory) * 100}%"></div>
                    </div>
                    <span class="stat-bar-count">${count}</span>
                </div>
            `).join('');
    }
    
    async savePosts() {
        try {
            console.log('保存数据:', this.posts.length, '篇文章');
            
            const response = await fetch('/api/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ posts: this.posts })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('保存成功', 'success');
                this.processMetadata();
                this.applyFilters();
                this.renderStats();
            } else {
                this.showToast('保存失败: ' + result.message, 'error');
            }
        } catch (error) {
            console.error('保存失败:', error);
            this.showToast('保存失败，请确保后端服务器正在运行', 'error');
            console.log('备用方案：手动保存到 data/posts.json 文件');
            console.log(JSON.stringify(this.posts, null, 2));
        }
    }
    
    closeModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
        this.editingPostId = null;
        this.deletingPostId = null;
        this.editingTagName = null;
    }
    
    showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type} show`;
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
    
    formatDate(dateString) {
        if (!dateString) return '-';
        
        const date = new Date(dateString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hour = String(date.getHours()).padStart(2, '0');
        const minute = String(date.getMinutes()).padStart(2, '0');
        
        return `${year}-${month}-${day} ${hour}:${minute}`;
    }
    
    // 评论管理相关方法
    renderComments() {
        this.renderCommentFilters();
        this.renderCommentsTable();
        this.renderCommentsPagination();
    }
    
    renderCommentFilters() {
        const articleFilter = document.getElementById('comment-article-filter');
        articleFilter.innerHTML = '<option value="">全部文章</option>';
        this.posts.forEach(post => {
            articleFilter.innerHTML += `<option value="${post.id}">${this.escapeHtml(post.title)}</option>`;
        });
    }
    
    applyCommentFilters() {
        const searchTerm = document.getElementById('comment-search-input').value.toLowerCase();
        const articleFilter = document.getElementById('comment-article-filter').value;
        
        this.filteredComments = this.allComments.filter(comment => {
            if (searchTerm) {
                const searchIn = (comment.author + ' ' + comment.content).toLowerCase();
                if (!searchIn.includes(searchTerm)) return false;
            }
            
            if (articleFilter && comment.postId !== parseInt(articleFilter)) return false;
            
            return true;
        });
        
        this.currentCommentPage = 1;
        this.renderCommentsTable();
        this.renderCommentsPagination();
    }
    
    renderCommentsTable() {
        const tbody = document.getElementById('comments-table-body');
        const start = (this.currentCommentPage - 1) * this.commentPageSize;
        const end = start + this.commentPageSize;
        const pageComments = this.filteredComments.slice(start, end);
        
        tbody.innerHTML = pageComments.map(comment => `
            <tr>
                <td>
                    <input type="checkbox" class="comment-checkbox" data-post-id="${comment.postId}" data-comment-id="${comment.id}" 
                        ${this.selectedCommentIds.has(`${comment.postId}-${comment.id}`) ? 'checked' : ''}>
                </td>
                <td>${comment.id}</td>
                <td>
                    <strong>${this.escapeHtml(comment.postTitle)}</strong>
                </td>
                <td>${this.escapeHtml(comment.author)}</td>
                <td>
                    <div class="comment-preview">
                        ${this.escapeHtml(comment.content.length > 50 ? comment.content.slice(0, 50) + '...' : comment.content)}
                    </div>
                </td>
                <td>${this.formatDate(comment.date)}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn edit" onclick="admin.openCommentModal(${comment.postId}, ${comment.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-btn delete" onclick="admin.deleteComment(${comment.postId}, ${comment.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
        
        document.querySelectorAll('.comment-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const key = `${e.target.dataset.postId}-${e.target.dataset.commentId}`;
                if (e.target.checked) {
                    this.selectedCommentIds.add(key);
                } else {
                    this.selectedCommentIds.delete(key);
                }
            });
        });
    }
    
    renderCommentsPagination() {
        const totalPages = Math.ceil(this.filteredComments.length / this.commentPageSize);
        const pagination = document.getElementById('comments-pagination');
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }
        
        let html = '';
        
        html += `<button onclick="admin.goToCommentPage(${this.currentCommentPage - 1})" 
            ${this.currentCommentPage === 1 ? 'disabled' : ''}>
            <i class="fas fa-chevron-left"></i> 上一页
        </button>`;
        
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || 
                (i >= this.currentCommentPage - 2 && i <= this.currentCommentPage + 2)) {
                html += `<button onclick="admin.goToCommentPage(${i})" 
                    class="${i === this.currentCommentPage ? 'active' : ''}">${i}</button>`;
            } else if (i === this.currentCommentPage - 3 || i === this.currentCommentPage + 3) {
                html += `<span>...</span>`;
            }
        }
        
        html += `<button onclick="admin.goToCommentPage(${this.currentCommentPage + 1})" 
            ${this.currentCommentPage === totalPages ? 'disabled' : ''}>
            下一页 <i class="fas fa-chevron-right"></i>
        </button>`;
        
        pagination.innerHTML = html;
    }
    
    goToCommentPage(page) {
        const totalPages = Math.ceil(this.filteredComments.length / this.commentPageSize);
        if (page >= 1 && page <= totalPages) {
            this.currentCommentPage = page;
            this.renderCommentsTable();
            this.renderCommentsPagination();
        }
    }
    
    toggleSelectAllComments(checked) {
        const start = (this.currentCommentPage - 1) * this.commentPageSize;
        const end = start + this.commentPageSize;
        const pageComments = this.filteredComments.slice(start, end);
        
        pageComments.forEach(comment => {
            const key = `${comment.postId}-${comment.id}`;
            if (checked) {
                this.selectedCommentIds.add(key);
            } else {
                this.selectedCommentIds.delete(key);
            }
        });
        
        this.renderCommentsTable();
    }
    
    openCommentModal(postId, commentId) {
        const post = this.posts.find(p => p.id === postId);
        const comment = post.comments.find(c => c.id === commentId);
        
        if (post && comment) {
            this.editingComment = { postId, commentId };
            
            document.getElementById('comment-modal-title').textContent = '编辑评论';
            document.getElementById('comment-post-id').value = postId;
            document.getElementById('comment-id').value = commentId;
            document.getElementById('comment-article-title').value = post.title;
            document.getElementById('comment-author').value = comment.author;
            document.getElementById('comment-content').value = comment.content;
            
            document.getElementById('comment-modal').classList.add('active');
        }
    }
    
    saveComment() {
        const postId = parseInt(document.getElementById('comment-post-id').value);
        const commentId = parseInt(document.getElementById('comment-id').value);
        const author = document.getElementById('comment-author').value.trim();
        const content = document.getElementById('comment-content').value.trim();
        
        if (!author || !content) {
            this.showToast('请填写必填字段', 'error');
            return;
        }
        
        const post = this.posts.find(p => p.id === postId);
        if (post && post.comments) {
            const index = post.comments.findIndex(c => c.id === commentId);
            if (index !== -1) {
                post.comments[index] = {
                    ...post.comments[index],
                    author,
                    content,
                    updated_at: new Date().toISOString()
                };
                
                this.processMetadata();
                this.savePosts();
                this.closeModals();
                this.renderComments();
                this.showToast('评论更新成功', 'success');
            }
        }
    }
    
    deleteComment(postId, commentId) {
        if (confirm('确定要删除这条评论吗？')) {
            const post = this.posts.find(p => p.id === postId);
            if (post && post.comments) {
                post.comments = post.comments.filter(c => c.id !== commentId);
                
                this.processMetadata();
                this.savePosts();
                this.renderComments();
                this.showToast('评论删除成功', 'success');
            }
        }
    }
    
    batchDeleteComments() {
        if (this.selectedCommentIds.size === 0) {
            this.showToast('请先选择要删除的评论', 'error');
            return;
        }
        
        if (confirm(`确定要删除选中的 ${this.selectedCommentIds.size} 条评论吗？`)) {
            this.selectedCommentIds.forEach(key => {
                const [postId, commentId] = key.split('-').map(Number);
                const post = this.posts.find(p => p.id === postId);
                if (post && post.comments) {
                    post.comments = post.comments.filter(c => c.id !== commentId);
                }
            });
            
            this.selectedCommentIds.clear();
            this.processMetadata();
            this.savePosts();
            this.renderComments();
            this.showToast('评论删除成功', 'success');
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    logout() {
        if (confirm('确定要退出登录吗？')) {
            sessionStorage.removeItem('isLoggedIn');
            sessionStorage.removeItem('loginTime');
            window.location.href = 'login.html';
        }
    }
}

let admin;
document.addEventListener('DOMContentLoaded', () => {
    admin = new BlogAdmin();
});
