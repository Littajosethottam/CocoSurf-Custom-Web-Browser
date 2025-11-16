import sys
import json
import os
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtGui import QIcon

def resource_path(filename):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.argv[0])))
    return os.path.join(base_path, filename)

# --- Ad Blocker Interceptor ---
class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super(AdBlocker, self).__init__(parent)
        self.blocked_domains = [
            'doubleclick.net',
            'googlesyndication.com',
            'adservice.google.com',
            'ads.yahoo.com',
            'facebook.com/tr/',
            'taboola.com',
            'outbrain.com',
            'adnxs.com',
            'zedo.com',
            'moatads.com',
            'criteo.net',
        ]

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        for domain in self.blocked_domains:
            if domain in url:
                print(f'🚫 Blocked: {url}')
                info.block(True)
                return

# --- Bookmark Manager ---
class BookmarkManager:
    def __init__(self, filename='bookmarks.json'):
        self.filename = filename
        self.bookmarks = self.load_bookmarks()

    def load_bookmarks(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_bookmarks(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.bookmarks, f, indent=2, ensure_ascii=False)

    def add_bookmark(self, title, url):
        bookmark = {'title': title, 'url': url}
        if bookmark not in self.bookmarks:
            self.bookmarks.append(bookmark)
            self.save_bookmarks()
            return True
        return False

    def remove_bookmark(self, url):
        self.bookmarks = [b for b in self.bookmarks if b['url'] != url]
        self.save_bookmarks()

    def get_bookmarks(self):
        return self.bookmarks

# --- Browser Tab Widget ---
class BrowserTab(QWebEngineView):
    def __init__(self, parent=None):
        super(BrowserTab, self).__init__(parent)
        self.parent = parent

    def createWindow(self, window_type):
        if self.parent:
            return self.parent.add_new_tab()
        return None

# --- Main Browser Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('CocoSurf')
        self.setWindowIcon(QIcon(resource_path('CocoSurf.png'))) # you can change filename if needed
        self.showMaximized()

        self.bookmark_manager = BookmarkManager()

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.setCentralWidget(self.tabs)

        navbar = QToolBar('Navigation')
        navbar.setMovable(False)
        self.addToolBar(navbar)

        back_btn = QAction(self.style().standardIcon(QStyle.SP_ArrowBack), '', self)
        back_btn.triggered.connect(lambda: self.current_browser().back())
        navbar.addAction(back_btn)

        forward_btn = QAction(self.style().standardIcon(QStyle.SP_ArrowForward), '', self)
        forward_btn.triggered.connect(lambda: self.current_browser().forward())
        navbar.addAction(forward_btn)

        reload_btn = QAction(self.style().standardIcon(QStyle.SP_BrowserReload), '', self)
        reload_btn.triggered.connect(lambda: self.current_browser().reload())
        navbar.addAction(reload_btn)

        home_btn = QAction(self.style().standardIcon(QStyle.SP_DesktopIcon), '', self)
        home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(home_btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        bookmark_btn = QAction('⭐', self)
        bookmark_btn.triggered.connect(self.add_bookmark)
        navbar.addAction(bookmark_btn)

        show_bookmarks_btn = QAction('📚', self)
        show_bookmarks_btn.triggered.connect(self.show_bookmarks)
        navbar.addAction(show_bookmarks_btn)

        new_tab_btn = QAction('➕', self)
        new_tab_btn.setShortcut('Ctrl+T')
        new_tab_btn.triggered.connect(lambda: self.add_new_tab(QUrl('https://google.com')))
        navbar.addAction(new_tab_btn)

        self.add_new_tab(QUrl('https://google.com'), 'Home')

    def add_new_tab(self, qurl=None, label='New Tab'):
        if qurl is None:
            qurl = QUrl('https://google.com')

        browser = BrowserTab(self)
        browser.setUrl(qurl)

        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

        browser.urlChanged.connect(lambda qurl, browser=browser:
                                   self.update_urlbar(qurl, browser))

        browser.loadFinished.connect(lambda _, i=i, browser=browser:
                                     self.tabs.setTabText(i, browser.page().title()[:20]))

        return browser

    def current_browser(self):
        return self.tabs.currentWidget()

    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            return
        self.tabs.removeTab(i)

    def current_tab_changed(self, i):
        qurl = self.current_browser().url()
        self.update_urlbar(qurl, self.current_browser())

    def update_urlbar(self, qurl, browser=None):
        if browser != self.current_browser():
            return
        self.url_bar.setText(qurl.toString())

    def navigate_home(self):
        home_path = resource_path("home.html")
        print("Homepage path is:", home_path)  # Diagnostic print to show where it's looking
        if os.path.exists(home_path):
            print("Found home.html, trying to load it...")
            self.current_browser().setUrl(QUrl.fromLocalFile(home_path))
        else:
            print("home.html NOT found, loading Google.com instead...")
            self.current_browser().setUrl(QUrl('https://google.com'))

    def navigate_to_url(self):
        url = self.url_bar.text()
        if ' ' in url or ('.' not in url and not url.startswith('http')):
            url = 'https://www.google.com/search?q=' + url.replace(' ', '+')
        elif not url.startswith('http'):
            url = 'http://' + url
        self.current_browser().setUrl(QUrl(url))

    def add_bookmark(self):
        browser = self.current_browser()
        title = browser.page().title()
        url = browser.url().toString()
        if self.bookmark_manager.add_bookmark(title, url):
            QMessageBox.information(self, 'Bookmark Added', f'Added: {title}')
        else:
            QMessageBox.information(self, 'Bookmark Exists', 'This page is already bookmarked!')

    def show_bookmarks(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Bookmarks')
        dialog.resize(600, 400)

        layout = QVBoxLayout()

        bookmark_list = QListWidget()
        bookmarks = self.bookmark_manager.get_bookmarks()
        for bookmark in bookmarks:
            item = QListWidgetItem(f"{bookmark['title']}")
            item.setData(Qt.UserRole, bookmark['url'])
            bookmark_list.addItem(item)

        bookmark_list.itemDoubleClicked.connect(
            lambda item: self.open_bookmark(item.data(Qt.UserRole), dialog))

        layout.addWidget(QLabel('Double-click to open, select and click Delete to remove:'))
        layout.addWidget(bookmark_list)

        button_layout = QHBoxLayout()

        open_btn = QPushButton('Open')
        open_btn.clicked.connect(lambda: self.open_bookmark(
            bookmark_list.currentItem().data(Qt.UserRole) if bookmark_list.currentItem() else None, dialog))

        delete_btn = QPushButton('Delete')
        delete_btn.clicked.connect(lambda: self.delete_bookmark(
            bookmark_list.currentItem().data(Qt.UserRole) if bookmark_list.currentItem() else None, bookmark_list))

        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dialog.close)

        button_layout.addWidget(open_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec_()

    def open_bookmark(self, url, dialog=None):
        if url:
            self.add_new_tab(QUrl(url))
            if dialog:
                dialog.close()

    def delete_bookmark(self, url, list_widget):
        if url:
            self.bookmark_manager.remove_bookmark(url)
            for i in range(list_widget.count()):
                if list_widget.item(i).data(Qt.UserRole) == url:
                    list_widget.takeItem(i)
                    break
            QMessageBox.information(self, 'Bookmark Deleted', 'Bookmark removed successfully!')

# --- Application Setup ---
app = QApplication(sys.argv)
QApplication.setApplicationName('CocoSurf')

profile = QWebEngineProfile.defaultProfile()
profile.setUrlRequestInterceptor(AdBlocker())

window = MainWindow()
sys.exit(app.exec_())
