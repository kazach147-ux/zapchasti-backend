from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton
from kivy.metrics import dp
from kivy.network.urlrequest import UrlRequest
from kivymd.app import MDApp
from kivy.clock import Clock
from urllib.parse import quote
from store import Store
from search_dropdown import SearchDropdown

class ShopHeader(MDBoxLayout):
    def __init__(self, show_back=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(65)
        self.md_bg_color = Store.COLOR_HEADER
        self.padding = [dp(10), dp(5), dp(10), dp(5)]
        self._search_event = None
        self._cache = {}
        
        self.main_row = MDBoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
        
        if show_back:
            self.main_row.add_widget(MDIconButton(
                icon="arrow-left",
                theme_icon_color="Custom",
                icon_color=(1, 1, 1, 1),
                on_release=self.go_back
            ))

        self.search_field = MDTextField(
            hint_text=Store.get_text("search", "Поиск..."),
            mode="round",
            fill_color_normal=(0.22, 0.22, 0.25, 1),
            line_color_normal=(0, 0, 0, 0),
            line_color_focus=(0, 0, 0, 0),
            radius=[20, 20, 20, 20],
            font_size=dp(14)
        )
        self.search_field.bind(text=self.on_search_text)
        
        self.mag_btn = MDIconButton(
            icon="magnify",
            theme_icon_color="Custom",
            icon_color=(1, 0.8, 0, 1),
            on_release=lambda x: self.search_confirm()
        )
        
        self.main_row.add_widget(self.search_field)
        self.main_row.add_widget(self.mag_btn)
        self.add_widget(self.main_row)
        self.dropdown = SearchDropdown()

    def on_search_text(self, instance, text):
        val = text.strip()
        if len(val) < 3:
            self.dropdown.dismiss()
            return
            
        if val in self._cache:
            self.handle_res(self._cache[val])
            return

        if self._search_event:
            self._search_event.cancel()
        self._search_event = Clock.schedule_once(lambda dt: self.perform_search(val), 0.4)

    def perform_search(self, query):
        words = query.split()
        clean_query = " ".join(words)
        url = f"{Store.SERVER_URL}/api/products?search={quote(clean_query)}&limit=10"
        UrlRequest(url, on_success=lambda req, res: self.save_and_show(query, res), timeout=5)

    def save_and_show(self, query, res):
        if res and isinstance(res, list):
            self._cache[query] = res
            if len(self._cache) > 30:
                self._cache.pop(next(iter(self._cache)))
            self.handle_res(res)

    def handle_res(self, res):
        if res and len(res) > 0:
            self.dropdown.open_under(self.search_field, res, self.select_product)
        else:
            self.dropdown.dismiss()

    def select_product(self, prod):
        self.dropdown.dismiss()
        self.search_field.text = ""
        app = MDApp.get_running_app()
        app.product_scr.update_data(prod)
        app.home_sm.current = 'product_details'

    def search_confirm(self):
        text = self.search_field.text.strip()
        if text:
            self.dropdown.dismiss()
            app = MDApp.get_running_app()
            app.catalog_scr.search_query = text
            app.home_sm.current = 'catalog'

    def go_back(self, *args):
        self.dropdown.dismiss()
        self.search_field.text = ""
        MDApp.get_running_app().home_sm.current = 'main'

    def clear_on_screen_change(self):
        self.search_field.text = ""
        self.dropdown.dismiss()