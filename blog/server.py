from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from datetime import datetime

POSTS_FILE = 'data/posts.json'

class BlogHandler(BaseHTTPRequestHandler):
    def _load_posts(self):
        print("[DEBUG] Loading posts...")
        with open(POSTS_FILE, 'r', encoding='utf-8') as f:
            posts = json.load(f)
        print(f"[DEBUG] Loaded {len(posts)} posts")
        return posts
    
    def _save_posts(self, posts):
        with open(POSTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
    
    def do_GET(self):
        if self.path.startswith('/api/comments/'):
            try:
                post_id = int(self.path.split('/api/comments/')[1])
                posts = self._load_posts()
                post = next((p for p in posts if p['id'] == post_id), None)
                if post:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True, 'comments': post.get('comments', [])}).encode('utf-8'))
                else:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': False, 'message': '文章不存在'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'message': str(e)}).encode('utf-8'))
        elif self.path == '/' or self.path == '/index.html':
            self.serve_file('index.html', 'text/html')
        elif self.path == '/index-minimal.html':
            self.serve_file('index-minimal.html', 'text/html')
        elif self.path == '/admin.html':
            self.serve_file('admin.html', 'text/html')
        elif self.path.startswith('/css/'):
            self.serve_file(self.path[1:], 'text/css')
        elif self.path.startswith('/js/'):
            self.serve_file(self.path[1:], 'application/javascript')
        elif self.path == '/data/posts.json':
            self.serve_file('data/posts.json', 'application/json')
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        if self.path == '/api/comments':
            try:
                data = json.loads(post_data.decode('utf-8'))
                post_id = data.get('postId')
                author = data.get('author', '匿名用户').strip()
                content = data.get('content', '').strip()
                
                if not post_id or not content:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': False, 'message': '缺少必要参数'}).encode('utf-8'))
                    return
                
                posts = self._load_posts()
                post = next((p for p in posts if p['id'] == post_id), None)
                
                if not post:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': False, 'message': '文章不存在'}).encode('utf-8'))
                    return
                
                if 'comments' not in post:
                    post['comments'] = []
                
                new_comment = {
                    'id': len(post['comments']) + 1,
                    'author': author if author else '匿名用户',
                    'content': content,
                    'date': datetime.now().isoformat()
                }
                
                post['comments'].append(new_comment)
                self._save_posts(posts)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'comment': new_comment}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'message': str(e)}).encode('utf-8'))
        elif self.path == '/api/save':
            try:
                data = json.loads(post_data.decode('utf-8'))
                posts = data.get('posts', [])
                
                self._save_posts(posts)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'message': '保存成功'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'message': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def serve_file(self, path, content_type):
        try:
            with open(path, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

def run_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, BlogHandler)
    print('Server running at http://localhost:8000/')
    print('Admin page: http://localhost:8000/admin.html')
    print('Press Ctrl+C to stop server')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped')
        httpd.shutdown()

if __name__ == '__main__':
    run_server()
