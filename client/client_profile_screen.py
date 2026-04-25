import webbrowser
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.datatables import MDDataTable
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from store import Store

class ClientProfileScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.render_main()
        Store.add_observer(self.update_ui_texts)

    def render_main(self):
        self.clear_widgets()
        self.layout = MDBoxLayout(orientation="vertical", md_bg_color=Store.COLOR_BG)
        
        self.header = MDBoxLayout(size_hint_y=None, height=dp(55), padding=dp(10), md_bg_color=Store.COLOR_HEADER)
        self.title_label = MDLabel(halign="center", bold=True, theme_text_color="Custom", text_color=Store.COLOR_TEXT_LIGHT)
        self.header.add_widget(self.title_label)
        self.layout.add_widget(self.header)

        scroll = ScrollView()
        self.container = MDBoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15), adaptive_height=True)

        self.fio = MDTextField(mode="fill", fill_color_normal=Store.COLOR_CARD, radius=[20, 20, 20, 20])
        self.phone = MDTextField(mode="fill", fill_color_normal=Store.COLOR_CARD, radius=[20, 20, 20, 20])
        self.viber = MDTextField(mode="fill", fill_color_normal=Store.COLOR_CARD, radius=[20, 20, 20, 20])
        self.email = MDTextField(mode="fill", fill_color_normal=Store.COLOR_CARD, radius=[20, 20, 20, 20])
        self.city = MDTextField(mode="fill", fill_color_normal=Store.COLOR_CARD, radius=[20, 20, 20, 20])
        self.warehouse = MDTextField(mode="fill", fill_color_normal=Store.COLOR_CARD, radius=[20, 20, 20, 20])

        self.btn_save = MDFlatButton(size_hint_x=1, height=dp(50), md_bg_color=Store.COLOR_ACCENT, text_color=(1, 1, 1, 1), on_release=self.save_data)
        self.btn_viber = MDFlatButton(size_hint_x=1, height=dp(50), md_bg_color=(0.5, 0.4, 0.7, 1), text_color=(1, 1, 1, 1), on_release=self.open_viber)
        self.btn_call = MDFlatButton(size_hint_x=1, height=dp(50), md_bg_color=(0.2, 0.6, 0.2, 1), text_color=(1, 1, 1, 1), on_release=self.make_call)

        self.container.add_widget(self.fio)
        self.container.add_widget(self.phone)
        self.container.add_widget(self.viber)
        self.container.add_widget(self.email)
        self.container.add_widget(self.city)
        self.container.add_widget(self.warehouse)
        self.container.add_widget(self.btn_save)
        self.container.add_widget(self.btn_viber)
        self.container.add_widget(self.btn_call)

        self.orders_table = MDDataTable(
            size_hint=(1, None), height=dp(300),
            column_data=[("№", dp(30)), ("СУММА", dp(40)), ("СТАТУС", dp(60))],
            row_data=[]
        )
        self.container.add_widget(self.orders_table)
        
        scroll.add_widget(self.container)
        self.layout.add_widget(scroll)
        self.add_widget(self.layout)
        self.update_ui_texts()

    def update_ui_texts(self, *args):
        self.title_label.text = "ЛИЧНЫЙ КАБИНЕТ"
        self.fio.hint_text = "ФИО"
        self.phone.hint_text = "ТЕЛЕФОН"
        self.viber.hint_text = "VIBER"
        self.email.hint_text = "EMAIL"
        self.city.hint_text = "ГОРОД"
        self.warehouse.hint_text = "ОТДЕЛЕНИЕ"
        self.btn_save.text = "СОХРАНИТЬ"
        self.btn_viber.text = "НАПИСАТЬ В VIBER"
        self.btn_call.text = "ПОЗВОНИТЬ"

    def on_enter(self):
        data = Store.get_user_data()
        self.fio.text = data.get("fio", "")
        self.phone.text = data.get("phone", "")
        self.viber.text = data.get("viber", "")
        self.email.text = data.get("email", "")
        self.city.text = data.get("city", "")
        self.warehouse.text = data.get("warehouse", "")

    def save_data(self, *args):
        data = {
            "fio": self.fio.text,
            "phone": self.phone.text,
            "viber": self.viber.text,
            "email": self.email.text,
            "city": self.city.text,
            "warehouse": self.warehouse.text
        }
        Store.save_user_data(data)
        self.fio.text = ""
        self.phone.text = ""
        self.viber.text = ""
        self.email.text = ""
        self.city.text = ""
        self.warehouse.text = ""

    def open_viber(self, *args):
        webbrowser.open("viber://chat?number=+380673160809")

    def make_call(self, *args):
        webbrowser.open("tel:+380673160809")