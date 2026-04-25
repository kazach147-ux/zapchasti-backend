import threading
import webbrowser
from kivy.app import App
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.recycleview import RecycleView
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.factory import Factory
from kivy.clock import Clock
from store import Store
from smart_image import SmartImage

class PhoneMaskTextField(MDTextField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._updating = False
        self.bind(text=self.on_text_change)

    def on_text_change(self, instance, value):
        if self._updating: return
        self._updating = True
        cleaned = ''.join(c for c in value if c.isdigit())
        if cleaned.startswith('38'): cleaned = cleaned[2:]
        if cleaned.startswith('0'): cleaned = cleaned[1:]
        cleaned = cleaned[:9]
        formatted = "+380"
        if len(cleaned) > 0: formatted += " (" + cleaned[:2]
        if len(cleaned) > 2: formatted += ") " + cleaned[2:5]
        if len(cleaned) > 5: formatted += "-" + cleaned[5:7]
        if len(cleaned) > 7: formatted += "-" + cleaned[7:]
        self.text = formatted
        Clock.schedule_once(self._set_cursor_end, 0)
        self._updating = False

    def _set_cursor_end(self, dt):
        self.cursor = (len(self.text), 0)

    def get_clean_phone(self):
        return ''.join(c for c in self.text if c.isdigit())

class CartItemCard(RecycleDataViewBehavior, MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(90)
        self.padding = dp(10)
        self.spacing = dp(10)
        self.md_bg_color = Store.COLOR_CARD
        self.radius = [20]
        self.img = SmartImage(size_hint=(None, 1), width=dp(70))
        info = MDBoxLayout(orientation='vertical')
        self.name_label = MDLabel(text="", theme_text_color="Custom", text_color=(1,1,1,1), font_style="Caption", bold=True)
        self.price_label = MDLabel(text="", theme_text_color="Custom", text_color=Store.COLOR_ACCENT, font_style="Caption")
        info.add_widget(self.name_label)
        info.add_widget(self.price_label)
        controls = MDBoxLayout(orientation='horizontal', size_hint_x=None, width=dp(170), spacing=dp(5))
        self.minus = MDIconButton(icon="minus", size_hint=(None,None), size=(dp(40),dp(40)))
        self.qty_label = MDLabel(text="1", halign="center", theme_text_color="Custom", text_color=(1,1,1,1), size_hint_x=None, width=dp(30))
        self.plus = MDIconButton(icon="plus", size_hint=(None,None), size=(dp(40),dp(40)))
        self.btn_delete = MDIconButton(icon="trash-can-outline", theme_icon_color="Custom", icon_color=(0.8, 0.2, 0.2, 1))
        controls.add_widget(self.minus)
        controls.add_widget(self.qty_label)
        controls.add_widget(self.plus)
        controls.add_widget(self.btn_delete)
        self.add_widget(self.img)
        self.add_widget(info)
        self.add_widget(controls)
        self.minus.bind(on_release=lambda x: self.change_qty(-1))
        self.plus.bind(on_release=lambda x: self.change_qty(1))
        self.btn_delete.bind(on_release=self.remove_item)

    def refresh_view_attrs(self, rv, index, data):
        self.p_id = data.get('id')
        self.img.source = data.get('image')
        self.name_label.text = data.get('name')
        self.price_label.text = data.get('price_text')
        self.qty_label.text = str(data.get('qty'))
        self.minus.disabled = data.get('qty', 1) <= 1
        return super().refresh_view_attrs(rv, index, data)

    def change_qty(self, delta):
        Store.update_cart_qty(self.p_id, Store.get_item_qty(self.p_id) + delta)
    
    def remove_item(self, inst):
        Store.remove_from_cart(self.p_id)

Factory.register('CartItemCard', cls=CartItemCard)

class CartScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.step = 1
        self.delivery_type = "np"
        self.payment_method = "cod"
        self.selected_city_ref = None
        self.selected_wh_ref = None
        self._ignore_search = False
        self.render_main()
        Store.add_observer(self.update_data)

    def render_main(self):
        self.clear_widgets()
        layout = MDBoxLayout(orientation='vertical', md_bg_color=Store.COLOR_BG)
        
        self.header = MDBoxLayout(size_hint_y=None, height=dp(50), padding=[dp(10), 0], md_bg_color=Store.COLOR_HEADER)
        self.back_btn = MDIconButton(icon="arrow-left", theme_icon_color="Custom", icon_color=(1,1,1,1), on_release=self.go_back)
        self.header.add_widget(self.back_btn)
        layout.add_widget(self.header)
        
        self.content_stack = MDBoxLayout(orientation='vertical')
        self.rv = RecycleView()
        self.grid = RecycleGridLayout(cols=1, spacing=dp(10), padding=dp(10), size_hint_y=None, default_size=(None, dp(90)), default_size_hint=(1, None))
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.rv.add_widget(self.grid)
        self.rv.viewclass = 'CartItemCard'
        
        self.form_scroll = ScrollView()
        self.form_container = MDBoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), adaptive_height=True)
        self.f_fio = MDTextField(hint_text="ПІБ")
        self.f_phone = PhoneMaskTextField(hint_text="Телефон *")
        self.f_viber = MDTextField(hint_text="Viber")
        self.f_city = MDTextField(hint_text="Місто *")
        self.f_city.bind(text=lambda ins, txt: self.search_cities(txt))
        self.f_wh = MDTextField(hint_text="Відділення *")
        self.f_wh.bind(focus=lambda ins, fcs: self.search_whs(fcs) if fcs else None)
        self.f_comment = MDTextField(hint_text="Коментар")
        
        self.menu_city = MDDropdownMenu(caller=self.f_city, items=[], width_mult=6, max_height=dp(300))
        self.menu_wh = MDDropdownMenu(caller=self.f_wh, items=[], width_mult=6, max_height=dp(300))
        
        self.pay_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        self.check_cod = CheckBox(group='pay', active=True)
        self.check_card = CheckBox(group='pay')
        self.check_cod.bind(active=lambda ch, act: setattr(self, 'payment_method', 'cod') if act else None)
        self.check_card.bind(active=lambda ch, act: setattr(self, 'payment_method', 'card') if act else None)
        self.pay_box.add_widget(self.check_cod); self.pay_box.add_widget(MDLabel(text="Накладений"))
        self.pay_box.add_widget(self.check_card); self.pay_box.add_widget(MDLabel(text="Карткою"))
        
        for w in [self.f_fio, self.f_phone, self.f_viber, self.f_city, self.f_wh, self.f_comment, self.pay_box]:
            self.form_container.add_widget(w)
        self.form_scroll.add_widget(self.form_container)
        
        layout.add_widget(self.content_stack)
        
        footer_wrap = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(70))
        line = MDBoxLayout(size_hint_y=None, height=dp(1), md_bg_color=(0.3, 0.3, 0.3, 1))
        self.footer = MDBoxLayout(orientation='horizontal', padding=[dp(15), dp(5)], spacing=dp(10), md_bg_color=Store.COLOR_HEADER)
        
        self.total_label = MDLabel(text="", theme_text_color="Custom", text_color=Store.COLOR_ACCENT, bold=True, size_hint_x=0.4)
        
        self.back_shop_btn = MDIconButton(icon="cart-plus", theme_icon_color="Custom", icon_color=(1,1,1,1), on_release=self.go_back_to_shop)
        self.next_btn = MDFlatButton(md_bg_color=Store.COLOR_ACCENT, text_color=(1,1,1,1), text="ОФОРМИТИ", on_release=self.handle_action, size_hint_x=0.5)
        
        self.footer.add_widget(self.total_label)
        self.footer.add_widget(self.back_shop_btn)
        self.footer.add_widget(self.next_btn)
        
        footer_wrap.add_widget(line)
        footer_wrap.add_widget(self.footer)
        
        layout.add_widget(footer_wrap)
        self.add_widget(layout)
        self.sync_ui()

    def sync_ui(self):
        self.content_stack.clear_widgets()
        self.next_btn.disabled = False
        if self.step == 1:
            self.content_stack.add_widget(self.rv)
            self.back_btn.opacity = 0
            self.next_btn.text = "ОФОРМИТИ"
            self.back_shop_btn.disabled = False
            self.back_shop_btn.opacity = 1
        else:
            self.content_stack.add_widget(self.form_scroll)
            self.back_btn.opacity = 1
            self.next_btn.text = "ПІДТВЕРДИТИ"
            self.back_shop_btn.disabled = True
            self.back_shop_btn.opacity = 0
        self.update_data()

    def go_back(self, inst):
        if self.step == 2: self.step = 1; self.sync_ui()

    def go_back_to_shop(self, inst):
        app = App.get_running_app()
        if app and hasattr(app, 'nav'):
            app.nav.switch_tab('main')

    def handle_action(self, inst):
        if self.step == 1:
            if Store.get_cart(): self.step = 2; self.sync_ui()
        else: self.process_order()

    def search_cities(self, text):
        if self._ignore_search or len(text) < 3: return
        threading.Thread(target=self._async_search_city, args=(text,), daemon=True).start()

    def _async_search_city(self, text):
        print("CITY SEARCH START:", text)
        print("SERVER:", Store.SERVER_URL)
        try:
            cities = Store.get_cities_from_server(text)
            print("CITIES RESPONSE:", cities)
            Clock.schedule_once(lambda dt: self._open_city_menu(cities))
        except Exception as e:
            print("CITY ERROR:", e)

    def _open_city_menu(self, cities):
        self.menu_city.dismiss()
        self.menu_city.items = [{"text": c['name'], "viewclass": "OneLineListItem", "on_release": lambda x=c: self.select_city(x)} for c in cities]
        if self.menu_city.items: self.menu_city.open()

    def select_city(self, city):
        self._ignore_search = True
        self.f_city.text = city['name']
        self.selected_city_ref = city['ref']
        self.menu_city.dismiss()
        Clock.schedule_once(lambda dt: setattr(self, '_ignore_search', False), 0.5)

    def search_whs(self, focus):
        if focus and self.selected_city_ref:
            threading.Thread(target=self._async_search_wh, daemon=True).start()

    def _async_search_wh(self):
        whs = Store.get_warehouses_from_server(self.selected_city_ref)
        Clock.schedule_once(lambda dt: self._open_wh_menu(whs))

    def _open_wh_menu(self, whs):
        self.menu_wh.dismiss()
        self.menu_wh.items = [{"text": w['name'], "viewclass": "OneLineListItem", "on_release": lambda x=w: self.select_wh(x)} for w in whs]
        if self.menu_wh.items: self.menu_wh.open()

    def select_wh(self, wh):
        self.f_wh.text = wh['name']
        self.selected_wh_ref = wh['ref']
        self.menu_wh.dismiss()

    def update_data(self, *args):
        cart = Store.get_cart()
        self.rv.data = [{"id": p.get('id'), "image": Store.get_image_url(p.get("image")), "name": p.get('name', ''), "price_text": f"{p.get('price', 0)} ₴", "qty": p.get('qty', 1)} for p in cart]
        self.rv.refresh_from_data()
        self.total_label.text = f"{sum(p.get('price', 0) * p.get('qty', 1) for p in cart)} ₴"

    def process_order(self):
        cart = Store.get_cart()
        if not cart: return
        if len(self.f_phone.get_clean_phone()) < 9 or not self.f_city.text:
            MDDialog(title="Помилка", text="Заповніть обов'язковые поля").open()
            return
        if not self.selected_wh_ref:
            MDDialog(title="Помилка", text="Оберіть відділення").open()
            return
        
        self.next_btn.disabled = True
        items_list = [{"id": str(p.get('id', '')), "name": str(p.get('name', 'Товар')), "price": float(p.get('price', 0)), "qty": int(p.get('qty', 1))} for p in cart]
        
        order_data = {
            "fio": self.f_fio.text.strip(),
            "phone": self.f_phone.get_clean_phone(),
            "viber": self.f_viber.text.strip(),
            "city": self.f_city.text.strip(),
            "city_ref": self.selected_city_ref,
            "warehouse_ref": self.selected_wh_ref,
            "warehouse_desc": self.f_wh.text.strip() or None,
            "comment": self.f_comment.text.strip(),
            "delivery_type": "Нова Пошта",
            "total_price": float(sum(p.get('price', 0) * p.get('qty', 1) for p in cart)),
            "items": items_list,
            "payment_method": self.payment_method
        }
        
        res = Store.create_order(order_data)
        if res and res.get("status") == "success":
            pay_url = res.get("payment_url")
            Store.clear_cart()
            self.step = 1
            self.sync_ui()
            
            if pay_url:
                webbrowser.open(pay_url)
                MDDialog(title="Оплата", text="Відкриваємо сторінку оплати...").open()
            else:
                MDDialog(title="Успіх", text="Замовлення створено").open()
        else:
            self.next_btn.disabled = False
            MDDialog(title="Помилка", text="Помилка сервера").open()
