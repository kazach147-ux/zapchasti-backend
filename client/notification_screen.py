from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.uix.recycleview import RecycleView
from kivy.metrics import dp
from kivy.network.urlrequest import UrlRequest
from store import Store
from kivy.factory import Factory

class NotificationRow(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(70)
        self.padding = dp(10)
        self.md_bg_color = Store.COLOR_CARD
        self.radius = [10]
        self.title = MDLabel(text="", bold=True, theme_text_color="Custom", text_color=(1,1,1,1))
        self.msg = MDLabel(text="", font_style="Caption", theme_text_color="Custom", text_color=(0.7,0.7,0.7,1))
        self.add_widget(self.title)
        self.add_widget(self.msg)

    def refresh_view_attrs(self, rv, index, data):
        self.title.text = data['title']
        self.msg.text = data['message']
        return super().refresh_view_attrs(rv, index, data)

Factory.register('NotificationRow', cls=NotificationRow)

class NotificationScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation="vertical", md_bg_color=Store.COLOR_BG)
        header = MDBoxLayout(size_hint_y=None, height=dp(55), padding=dp(10), md_bg_color=Store.COLOR_HEADER)
        header.add_widget(MDLabel(text=Store.get_text("notifications").upper(), halign="center", bold=True, theme_text_color="Custom", text_color=Store.COLOR_TEXT_LIGHT))
        self.layout.add_widget(header)
        self.rv = RecycleView()
        self.rv.viewclass = 'NotificationRow'
        self.grid = Factory.RecycleBoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5), padding=dp(10), default_size=(None, dp(70)), default_size_hint=(1, None))
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.rv.add_widget(self.grid)
        self.layout.add_widget(self.rv)
        self.add_widget(self.layout)

    def on_enter(self):
        UrlRequest(f"{Store.SERVER_URL}/api/notifications", on_success=self.on_success)

    def on_success(self, req, result):
        self.rv.data = [{'title': f"ID: {n.get('order_id')} - {n.get('status')}", 'message': n.get('message', '')} for n in result]

    def update_lang(self):
        pass