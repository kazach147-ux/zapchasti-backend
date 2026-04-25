from urllib.parse import quote
from kivy.factory import Factory
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.app import MDApp
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.network.urlrequest import UrlRequest
from kivy.uix.recycleview import RecycleView
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from store import Store
from smart_image import SmartImage
from header_component import ShopHeader

class ProductCard(RecycleDataViewBehavior, MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(240)
        self.padding = dp(5)
        self.spacing = dp(2)
        self.md_bg_color = Store.COLOR_CARD
        self.radius = [20]
        self.touch_start_pos = None
        
        self.w_img = SmartImage(source="", size_hint_y=None, height=dp(130))
        self.w_name = MDLabel(
            text="", halign="center", theme_text_color="Custom",
            text_color=(1, 1, 1, 1), font_style="Caption", bold=True,
            font_size="11sp", adaptive_height=True, max_lines=2
        )
        self.w_price = MDLabel(
            text="", halign="center", theme_text_color="Custom",
            text_color=Store.COLOR_ACCENT, font_style="Body1", bold=True
        )
        self.btn_buy = MDFlatButton(
            text=Store.get_text("buy").upper(),
            pos_hint={"center_x": 0.5},
            md_bg_color=Store.COLOR_ACCENT,
            text_color=(1, 1, 1, 1),
            font_size="10sp"
        )
        self.btn_buy.bind(on_release=self.add_to_cart_action)
        
        self.add_widget(self.w_img)
        self.add_widget(self.w_name)
        self.add_widget(self.w_price)
        self.add_widget(self.btn_buy)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.product_data = data.get('product')
        self.w_img.source = data.get('image')
        self.w_name.text = data.get('name')
        self.w_price.text = data.get('price')
        self.open_func = data.get('open_func')
        self.btn_buy.text = Store.get_text("buy").upper()
        
        if index >= len(rv.data) - 10:
            scr = rv.parent.parent
            if hasattr(scr, 'check_and_load_more'):
                scr.check_and_load_more()
            
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.touch_start_pos = touch.pos
            if self.btn_buy.collide_point(*touch.pos):
                return self.btn_buy.on_touch_down(touch)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and self.touch_start_pos:
            dx = abs(touch.pos[0] - self.touch_start_pos[0])
            dy = abs(touch.pos[1] - self.touch_start_pos[1])
            if dx < 10 and dy < 10:
                if not self.btn_buy.collide_point(*touch.pos):
                    if hasattr(self, 'open_func') and self.open_func:
                        self.open_func(self.product_data)
                        return True
            self.touch_start_pos = None
        return super().on_touch_up(touch)

    def add_to_cart_action(self, inst):
        Store.add_to_cart(self.product_data)
        app = MDApp.get_running_app()
        if hasattr(app, 'cart_scr'):
            app.cart_scr.update_data()

class CatalogScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.category_id = None
        self.search_query = None
        self.page = 0
        self.loading = False
        self.no_more_data = False
        self.limit = 40
        self.requested_pages = set()
        Store.add_observer(self.retranslate_ui)
        self.render_catalog()

    def retranslate_ui(self, *args):
        if hasattr(self, 'header') and hasattr(self.header, 'search_field'):
            self.header.search_field.hint_text = Store.get_text("search").upper()
        if self.rv.data:
            self.refresh_data_lang()

    def refresh_data_lang(self):
        new_data = []
        for item in self.rv.data:
            p = item['product']
            name_val = str(p.get(f"name_{Store._lang}", p.get("name", "")))
            item["name"] = (name_val[:30] + "...") if len(name_val) > 33 else name_val
            item["price"] = f"{p.get('price')} {Store.get_text('currency')}"
            new_data.append(item)
        self.rv.data = new_data

    def render_catalog(self):
        self.clear_widgets()
        layout = MDBoxLayout(orientation="vertical", md_bg_color=Store.COLOR_BG)
        header_box = MDBoxLayout(size_hint_y=None, height=dp(55), spacing=dp(5), padding=[dp(5), 0, dp(10), 0], md_bg_color=Store.COLOR_HEADER)
        btn_back = MDIconButton(
            icon="arrow-left", 
            theme_icon_color="Custom", 
            icon_color=(1, 1, 1, 1),
            on_release=self.go_back
        )
        header_box.add_widget(btn_back)
        self.header = ShopHeader()
        header_box.add_widget(self.header)
        layout.add_widget(header_box)
        
        self.rv = RecycleView(
            scroll_distance=dp(30),
            scroll_timeout=100,
            bar_width=dp(2)
        )
        self.grid = RecycleGridLayout(
            cols=2, spacing=dp(10), padding=dp(10),
            default_size=(None, dp(240)), default_size_hint=(1, None),
            size_hint_y=None
        )
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.rv.add_widget(self.grid)
        self.rv.viewclass = 'ProductCard'
        layout.add_widget(self.rv)
        self.add_widget(layout)
        Window.bind(on_resize=self.update_grid_cols)

    def check_and_load_more(self):
        next_p = self.page + 1
        if not self.loading and not self.no_more_data and next_p not in self.requested_pages:
            self.page = next_p
            self.load_products()

    def go_back(self, inst):
        app = MDApp.get_running_app()
        if hasattr(self, 'header') and hasattr(self.header, 'search_field'):
            self.header.search_field.text = ""
        app.home_sm.current = 'main'

    def on_enter(self):
        if hasattr(self, 'header') and hasattr(self.header, 'search_field'):
            self.header.search_field.hint_text = Store.get_text("search").upper()
        if not self.rv.data:
            self.page = 0
            self.no_more_data = False
            self.requested_pages.clear()
            self.load_products()

    def load_products(self):
        if self.page in self.requested_pages and self.loading: return
        
        self.loading = True
        self.requested_pages.add(self.page)
        
        cached = Store.get_cached_products(
            offset=self.page * self.limit, 
            limit=self.limit, 
            category_id=self.category_id, 
            search=self.search_query
        )
        
        if cached:
            self.draw_products(None, cached, is_append=True)
            self.loading = False
            return
            
        url = f"{Store.SERVER_URL}/api/products?page={self.page + 1}&limit={self.limit}"
        if self.category_id: url += f"&category={self.category_id}"
        if self.search_query: url += f"&search={quote(self.search_query)}"
        
        UrlRequest(url, on_success=self.on_server_res, on_failure=self.handle_err, on_error=self.handle_err)

    def on_server_res(self, req, res):
        self.loading = False
        if res and isinstance(res, list) and len(res) > 0:
            Store.cache_products(res, self.category_id)
            self.draw_products(req, res, is_append=True)
        else:
            if self.page > 0:
                self.no_more_data = True

    def draw_products(self, req, res, is_append=False):
        items = []
        for p in res:
            name_val = str(p.get(f"name_{Store._lang}", p.get("name", "")))
            items.append({
                "image": Store.get_image_url(p.get("image")),
                "name": (name_val[:30] + "...") if len(name_val) > 33 else name_val,
                "price": f"{p.get('price')} {Store.get_text('currency')}",
                "product": p,
                "open_func": self.open_product
            })
        
        if is_append or self.rv.data:
            existing_ids = {str(x['product']['id']) for x in self.rv.data}
            unique_new = [i for i in items if str(i['product']['id']) not in existing_ids]
            if unique_new:
                self.rv.data.extend(unique_new)
        else:
            self.rv.data = items
        self.update_grid_cols()

    def handle_err(self, req, res):
        self.loading = False

    def update_grid_cols(self, *args):
        col_width = dp(170)
        self.grid.cols = max(2, int(Window.width / col_width))

    def open_product(self, product):
        app = MDApp.get_running_app()
        app.product_scr.update_data(product)
        app.home_sm.current = 'product_details'

Factory.register('ProductCard', cls=ProductCard)