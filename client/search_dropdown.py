from kivy.uix.modalview import ModalView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.core.window import Window
from store import Store
from smart_image import SmartImage

class SearchDropdown(ModalView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.auto_dismiss = True
        self.overlay_color = [0, 0, 0, 0]
        self.background = ""
        
        self.scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=0
        )
        self.container = MDBoxLayout(
            orientation='vertical',
            adaptive_height=True,
            md_bg_color=Store.COLOR_CARD
        )
        self.scroll.add_widget(self.container)
        self.add_widget(self.scroll)

    def open_under(self, target, results, callback):
        if self.parent:
            Window.remove_widget(self)
            
        self.container.clear_widgets()
        
        for p in results:
            item = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(60),
                padding=[dp(10), dp(5)],
                spacing=dp(10),
                md_bg_color=Store.COLOR_CARD
            )
            
            img = SmartImage(
                source=Store.get_image_url(p.get('image', '')),
                size_hint=(None, None),
                size=(dp(50), dp(50))
            )
            
            texts = MDBoxLayout(orientation="vertical")
            name = MDLabel(
                text=str(p.get('name', '')),
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
                font_style="Caption",
                shorten=True
            )
            price = MDLabel(
                text=f"{p.get('price')} грн",
                theme_text_color="Custom",
                text_color=Store.COLOR_ACCENT,
                font_style="Caption"
            )
            texts.add_widget(name)
            texts.add_widget(price)
            
            item.add_widget(img)
            item.add_widget(texts)
            
            item.bind(on_touch_down=lambda inst, touch, prod=p: self._handle_click(inst, touch, prod, callback))
            self.container.add_widget(item)

        self.width = target.width
        self.height = min(dp(300), len(results) * dp(61))
        
        wx, wy = target.to_window(target.x, target.y)
        self.pos = (wx, wy - self.height - dp(2))
        
        Window.add_widget(self)

    def _handle_click(self, instance, touch, prod, callback):
        if instance.collide_point(*touch.pos):
            callback(prod)
            self.dismiss()
            return True

    def dismiss(self, *args):
        if self.parent:
            Window.remove_widget(self)