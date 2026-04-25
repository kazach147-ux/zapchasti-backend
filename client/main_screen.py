import os
from urllib.parse import quote
from kivy.factory import Factory
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton
from kivymd.app import MDApp
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.network.urlrequest import UrlRequest
from kivy.uix.recycleview import RecycleView
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.scrollview import ScrollView
from kivymd.uix.label import MDIcon
from store import Store
from smart_image import SmartImage
from header_component import ShopHeader

class MainProductCard(RecycleDataViewBehavior, MDBoxLayout):
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
            text="",
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

class FolderTile(MDBoxLayout):
    def __init__(self, text, query, icon_name=None, image_source=None, is_special=True, is_catalog=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (None, None)
        self.size = (dp(110), dp(100))
        self.padding = dp(5)
        self.spacing = dp(2)
        self.radius = [15]
        self.touch_start_pos = None
        
        if is_special:
            self.md_bg_color = (1, 0.75, 0, 1)
            text_col = (0, 0, 0, 1)
        else:
            self.md_bg_color = (0.2, 0.2, 0.2, 1)
            text_col = (1, 1, 1, 1)
            
        if image_source:
            self.icon_box = MDBoxLayout(size_hint_y=0.6)
            self.icon_widget = SmartImage(
                source=image_source,
                size_hint=(None, None),
                size=(dp(55), dp(55)),
                pos_hint={"center_x": 0.5, "center_y": 0.5}
            )
            self.icon_box.add_widget(self.icon_widget)
            self.add_widget(self.icon_box)
        else:
            self.icon_widget = MDIcon(
                icon=icon_name if icon_name else "cog",
                halign="center",
                font_size="38sp",
                theme_text_color="Custom",
                text_color=text_col,
                size_hint_y=0.6
            )
            self.add_widget(self.icon_widget)
            
        self.name_lbl = MDLabel(
            text=text.upper(),
            halign="center",
            font_style="Caption",
            bold=True,
            font_size="9sp",
            theme_text_color="Custom",
            text_color=text_col,
            size_hint_y=0.4
        )
        self.add_widget(self.name_lbl)
        self.query = query
        self.is_catalog = is_catalog

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.touch_start_pos = touch.pos
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and self.touch_start_pos:
            dx = abs(touch.pos[0] - self.touch_start_pos[0])
            dy = abs(touch.pos[1] - self.touch_start_pos[1])
            if dx < 10 and dy < 10:
                app = MDApp.get_running_app()
                if self.is_catalog:
                    app.home_sm.current = 'catalog'
                else:
                    app.main_scr.set_filter(self.query)
                return True
            self.touch_start_pos = None
        return super().on_touch_up(touch)

class MainScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loading = False
        self.page = 0
        self.limit = 40
        self.no_more_data = False
        self.current_query = ""
        self.requested_pages = set()
        
        self.layout = MDBoxLayout(orientation="vertical", md_bg_color=Store.COLOR_BG)
        self.header = ShopHeader()
        self.layout.add_widget(self.header)
        
        self.ribbon_scroll = ScrollView(size_hint_y=None, height=dp(115), do_scroll_y=False)
        self.ribbon_box = MDBoxLayout(adaptive_width=True, padding=[dp(10), dp(5)], spacing=dp(10))
        self.ribbon_scroll.add_widget(self.ribbon_box)
        self.layout.add_widget(self.ribbon_scroll)
        
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
        self.rv.viewclass = 'MainProductCard'
        self.layout.add_widget(self.rv)
        
        self.add_widget(self.layout)
        Window.bind(on_resize=self.recalc_cols)
        Store.add_observer(self.retranslate_ui)

    def retranslate_ui(self, *args):
        if hasattr(self, 'header') and hasattr(self.header, 'search_field'):
            self.header.search_field.hint_text = Store.get_text("search").upper()
        self.load_categories()
        if self.rv.data:
            self.refresh_products_lang()

    def on_enter(self):
        if hasattr(self, 'header') and hasattr(self.header, 'search_field'):
            self.header.search_field.text = ""
            self.header.search_field.hint_text = Store.get_text("search").upper()
        
        self.page = 0
        self.no_more_data = False
        self.requested_pages.clear()
        
        cached_cats = Store.get_cached_categories()
        if cached_cats:
            self.render_folders(None, cached_cats)
        
        cached_prods = Store.get_cached_products(offset=0, limit=self.limit, search=self.current_query)
        if cached_prods:
            self.draw_products(None, cached_prods)

        self.load_categories()
        self.load_data()

    def load_categories(self):
        UrlRequest(f"{Store.SERVER_URL}/api/categories", on_success=self.on_cats_res)

    def on_cats_res(self, req, res):
        if res and isinstance(res, list):
            Store.cache_categories(res)
            self.render_folders(req, res)

    def render_folders(self, req, res):
        self.ribbon_box.clear_widgets()
        specials = [
            (Store.get_text("menu_new"), "tag=new", "star"),
            (Store.get_text("popular"), "tag=pop", "fire"),
            (Store.get_text("menu_sale"), "tag=sale", "percent")
        ]
        for name, query, icon in specials:
            self.ribbon_box.add_widget(FolderTile(text=name, query=query, icon_name=icon, is_special=True))
        
        self.ribbon_box.add_widget(FolderTile(text=Store.get_text("catalog"), query="", icon_name="format-list-bulleted", is_special=False, is_catalog=True))
        
        if isinstance(res, list):
            for cat in res:
                c_name = cat.get(f'name_{Store._lang}', cat.get('name', ''))
                c_img = cat.get('image', None)
                img_path = Store.get_image_url(c_img) if c_img else None
                self.ribbon_box.add_widget(FolderTile(text=c_name, query=f"category_id={cat.get('id')}", image_source=img_path, is_special=False))

    def set_filter(self, query):
        self.page = 0
        self.rv.data = []
        self.no_more_data = False
        self.requested_pages.clear()
        self.current_query = query
        self.load_data()

    def check_and_load_more(self):
        next_p = self.page + 1
        if not self.loading and not self.no_more_data and next_p not in self.requested_pages:
            self.page = next_p
            self.load_data()

    def load_data(self):
        if self.page in self.requested_pages and self.loading: return
        self.loading = True
        self.requested_pages.add(self.page)
        
        url = f"{Store.SERVER_URL}/api/products?page={self.page + 1}&limit={self.limit}"
        if self.current_query: url += f"&{self.current_query}"
        UrlRequest(url, on_success=self.on_server_res, on_failure=self.reset_loading, on_error=self.reset_loading)

    def on_server_res(self, req, res):
        self.loading = False
        if res and isinstance(res, list) and len(res) > 0:
            Store.cache_products(res)
            self.draw_products(req, res)
        else:
            if self.page > 0: self.no_more_data = True

    def reset_loading(self, req, res):
        self.loading = False

    def draw_products(self, req, res):
        new_items = []
        for p in res:
            name_val = str(p.get(f'name_{Store._lang}', p.get('name','')))
            new_items.append({
                "image": Store.get_image_url(p.get('image')),
                "name": (name_val[:30] + "...") if len(name_val) > 33 else name_val,
                "price": f"{p.get('price')} {Store.get_text('currency')}",
                "product": p,
                "open_func": self.open_p
            })
        
        existing_ids = {str(x['product']['id']) for x in self.rv.data}
        unique_new = [i for i in new_items if str(i['product']['id']) not in existing_ids]
        if unique_new:
            self.rv.data.extend(unique_new)
        self.recalc_cols()

    def refresh_products_lang(self):
        updated_data = []
        for item in self.rv.data:
            p = item.get('product')
            name_val = str(p.get(f'name_{Store._lang}', p.get('name','')))
            item["name"] = (name_val[:30] + "...") if len(name_val) > 33 else name_val
            item["price"] = f"{p.get('price')} {Store.get_text('currency')}"
            updated_data.append(item)
        self.rv.data = updated_data

    def recalc_cols(self, *args):
        col_width = dp(170)
        self.grid.cols = max(2, int(Window.width / col_width))

    def open_p(self, product):
        app = MDApp.get_running_app()
        app.product_scr.update_data(product)
        app.home_sm.current = 'product_details'

Factory.register('MainProductCard', cls=MainProductCard)
Factory.register('FolderTile', cls=FolderTile)