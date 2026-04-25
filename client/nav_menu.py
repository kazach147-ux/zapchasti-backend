from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivy.metrics import dp
from store import Store
from kivymd.app import MDApp

class NavMenu(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(65)
        self.padding = [dp(5), dp(2)]
        self.spacing = dp(5)
        self.md_bg_color = Store.COLOR_HEADER
        self.sm_manager = None

    def set_manager(self, sm):
        self.sm_manager = sm
        self.render_menu()

    def render_menu(self):
        self.clear_widgets()
        current = self.sm_manager.current if self.sm_manager else "main"
        items = [
            ("home", "main", "menu_home"),
            ("cart", "cart", "menu_cart"),
            ("account", "profile", "menu_profile"),
            ("translate", "settings", "menu_lang")
        ]
        for icon, screen, lang_key in items:
            box = MDBoxLayout(orientation="vertical", spacing=0)
            is_active = (current == screen)
            color = Store.COLOR_ACCENT if is_active else (0.5,0.5,0.5,1)

            btn = MDIconButton(
                icon=icon,
                theme_icon_color="Custom",
                icon_color=color,
                pos_hint={"center_x": 0.5},
                on_release=lambda inst, s=screen: self.change_screen(s)
            )
            lbl = MDLabel(
                text=Store.get_text(lang_key).upper(),
                theme_text_color="Custom",
                text_color=color,
                font_style="Caption",
                halign="center",
                size_hint_y=None,
                height=dp(15),
                font_size="10sp"
            )
            box.add_widget(btn)
            box.add_widget(lbl)
            self.add_widget(box)

    def change_screen(self, screen_name):
        if self.sm_manager:
            self.sm_manager.current = screen_name
            self.render_menu()