from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton, MDIconButton
from smart_image import SmartImage
from kivymd.uix.scrollview import MDScrollView
from kivy.uix.recycleview import RecycleView
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.metrics import dp
from kivy.core.window import Window
from kivymd.app import MDApp
from kivy.network.urlrequest import UrlRequest
from store import Store
from header_component import ShopHeader
from kivy.factory import Factory

class RelatedProductCard(RecycleDataViewBehavior, MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_x = None
        self.width = dp(140)
        self.md_bg_color = Store.COLOR_CARD
        self.radius = [20]
        self.padding = dp(5)
        self.spacing = dp(2)
        
        self.img = SmartImage(size_hint_y=None, height=dp(80))
        self.name_label = MDLabel(halign="center", font_style="Caption", theme_text_color="Custom", text_color=(1,1,1,1), size_hint_y=None, height=dp(40))
        self.price_label = MDLabel(halign="center", theme_text_color="Custom", text_color=Store.COLOR_ACCENT, font_style="Caption", bold=True)
        self.btn_buy = MDFlatButton(
            text="",
            pos_hint={"center_x": 0.5},
            md_bg_color=Store.COLOR_ACCENT,
            text_color=(1, 1, 1, 1),
            font_size="9sp",
            on_release=self.add_to_cart
        )
        
        self.add_widget(self.img)
        self.add_widget(self.name_label)
        self.add_widget(self.price_label)
        self.add_widget(self.btn_buy)

    def refresh_view_attrs(self, rv, index, data):
        self.product_data = data.get('product')
        self.img.source = data.get('image')
        self.name_label.text = data.get('name')
        self.price_label.text = data.get('price')
        self.open_func = data.get('open_func')
        self.btn_buy.text = Store.get_text("buy").upper()
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.btn_buy.collide_point(*touch.pos):
            if hasattr(self, 'open_func') and self.open_func:
                self.open_func(self.product_data)
                return True
        return super().on_touch_down(touch)

    def add_to_cart(self, inst):
        Store.add_to_cart(self.product_data)
        app = MDApp.get_running_app()
        if hasattr(app, 'cart_scr'):
            app.cart_scr.update_data()

class ProductScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.product_data = None
        Store.add_observer(self.update_data)
        self.render_main()

    def render_main(self):
        self.clear_widgets()
        layout = MDBoxLayout(orientation='vertical', md_bg_color=Store.COLOR_BG)
        
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

        self.main_scroll = MDScrollView()
        content = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing=dp(15), padding=dp(15))

        self.img = SmartImage(size_hint_y=None, height=dp(300))
        content.add_widget(self.img)

        self.title_label = MDLabel(theme_text_color="Custom", text_color=(1,1,1,1), font_style="H6", bold=True, adaptive_height=True)
        content.add_widget(self.title_label)

        self.price_label = MDLabel(theme_text_color="Custom", text_color=Store.COLOR_ACCENT, font_style="H5", bold=True, adaptive_height=True)
        content.add_widget(self.price_label)

        self.btn_buy = MDFlatButton(
            text="",
            size_hint_x=1, height=dp(50),
            md_bg_color=Store.COLOR_ACCENT,
            text_color=(1, 1, 1, 1),
            on_release=self.add_to_cart
        )
        content.add_widget(self.btn_buy)

        self.related_label = MDLabel(text="", theme_text_color="Custom", text_color=(0.7,0.7,0.7,1), font_style="Subtitle2", adaptive_height=True)
        content.add_widget(self.related_label)
        
        self.related_rv = RecycleView(size_hint_y=None, height=dp(180))
        self.related_grid = RecycleGridLayout(rows=1, spacing=dp(10), size_hint_x=None, default_size=(dp(140), None), default_size_hint=(None, 1))
        self.related_grid.bind(minimum_width=self.related_grid.setter('width'))
        self.related_rv.add_widget(self.related_grid)
        self.related_rv.viewclass = 'RelatedProductCard'
        content.add_widget(self.related_rv)

        self.main_scroll.add_widget(content)
        layout.add_widget(self.main_scroll)
        self.add_widget(layout)

    def go_back(self, inst):
        app = MDApp.get_running_app()
        app.home_sm.current = 'catalog'

    def update_data(self, data=None):
        if data: self.product_data = data
        if not self.product_data: return
        
        self.img.source = Store.get_image_url(self.product_data.get('image'))
        self.title_label.text = self.product_data.get(f'name_{Store._lang}', self.product_data.get('name', ''))
        self.price_label.text = f"{self.product_data.get('price')} {Store.get_text('currency')}"
        self.btn_buy.text = Store.get_text("buy").upper()
        self.related_label.text = Store.get_text("with_this_item").upper()
        self.main_scroll.scroll_y = 1
        self.load_related(self.product_data.get('category_id'))

    def add_to_cart(self, inst):
        if self.product_data:
            Store.add_to_cart(self.product_data)
            app = MDApp.get_running_app()
            if hasattr(app, 'cart_scr'):
                app.cart_scr.update_data()

    def load_related(self, cat_id):
        if not cat_id: return
        url = f"{Store.SERVER_URL}/api/products?category_id={cat_id}&limit=10"
        UrlRequest(url, on_success=self.on_related_success)

    def on_related_success(self, req, res):
        rv_data = []
        if res and isinstance(res, list):
            for p in res:
                if str(p.get('id')) == str(self.product_data.get('id')): continue
                name_val = p.get(f'name_{Store._lang}', p.get('name', ''))
                rv_data.append({
                    "image": Store.get_image_url(p.get("image")),
                    "name": (name_val[:20] + "...") if len(name_val) > 23 else name_val,
                    "price": f"{p.get('price')} {Store.get_text('currency')}",
                    "product": p,
                    "open_func": self.update_data
                })
        self.related_rv.data = rv_data

Factory.register('RelatedProductCard', cls=RelatedProductCard)