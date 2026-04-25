from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.label import MDLabel
from kivy.metrics import dp
from store import Store
from kivymd.app import MDApp

class SettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.render_settings()

    def on_enter(self):
        self.render_settings()

    def render_settings(self):
        self.clear_widgets()
        layout = MDBoxLayout(orientation="vertical", md_bg_color=Store.COLOR_BG)
        
        header = MDBoxLayout(size_hint_y=None, height=dp(55), md_bg_color=Store.COLOR_HEADER, padding=dp(10))
        header.add_widget(MDLabel(text=Store.get_text("settings").upper(), halign="center", bold=True, theme_text_color="Custom", text_color=Store.COLOR_TEXT_LIGHT))
        layout.add_widget(header)

        content = MDBoxLayout(orientation="vertical", padding=dp(20), spacing=dp(20))
        
        lbl = MDLabel(text=Store.get_text("choose_language").upper(), halign="center", theme_text_color="Custom", text_color=Store.COLOR_TEXT_LIGHT, size_hint_y=None, height=dp(50))
        content.add_widget(lbl)
        
        for lang, name in [("ua", "УКРАЇНСЬКА"), ("ru", "РУССКИЙ")]:
            btn = MDFlatButton(
                text=name, size_hint_x=1, height=dp(50),
                md_bg_color=Store.COLOR_ACCENT if Store._lang == lang else Store.COLOR_CARD,
                text_color=(1, 1, 1, 1),
                on_release=lambda x, l=lang: self.change_lang(l)
            )
            content.add_widget(btn)
        
        content.add_widget(MDBoxLayout())
        layout.add_widget(content)
        self.add_widget(layout)

    def change_lang(self, lang):
        Store.set_lang(lang)
        app = MDApp.get_running_app()
        if hasattr(app, 'refresh_all_texts'):
            app.refresh_all_texts()
        self.render_settings()