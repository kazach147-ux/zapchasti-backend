import os
from kivymd.app import MDApp
from kivy.core.window import Window
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivy.uix.screenmanager import ScreenManager
from store import Store

from main_screen import MainScreen
from catalog_screen import CatalogScreen
from product_screen import ProductScreen
from cart_screen import CartScreen
from client_profile_screen import ClientProfileScreen
from settings_screen import SettingsScreen

class MainApp(MDApp):
    def build(self):
        Store.init()
        print(f"[MAIN] STARTING APP. SERVER: {Store.SERVER_URL}")
        Window.softinput_mode = "below_target"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        
        self.nav = MDBottomNavigation(use_text=True)
        self.nav.bind(on_tab_press=self.clear_search_only)
        
        self.home_sm = ScreenManager()
        self.main_scr = MainScreen(name='main')
        self.catalog_scr = CatalogScreen(name='catalog')
        self.product_scr = ProductScreen(name='product_details')
        
        self.home_sm.add_widget(self.main_scr)
        self.home_sm.add_widget(self.catalog_scr)
        self.home_sm.add_widget(self.product_scr)
        
        self.item_main = MDBottomNavigationItem(
            self.home_sm, name='main', 
            text=Store.get_text("menu_home").upper(), icon="home"
        )
        
        self.cart_scr = CartScreen(name='cart')
        self.item_cart = MDBottomNavigationItem(
            self.cart_scr, name='cart', 
            text=Store.get_text("menu_cart").upper(), icon="cart"
        )
        self.item_cart.bind(on_tab_press=self.on_cart_tab)

        self.profile_scr = ClientProfileScreen(name='profile')
        self.item_profile = MDBottomNavigationItem(
            self.profile_scr, name='profile', 
            text=Store.get_text("menu_profile").upper(), icon="account"
        )
        self.item_profile.bind(on_tab_press=self.clear_search_only)

        self.settings_scr = SettingsScreen(name='settings')
        self.item_lang = MDBottomNavigationItem(
            self.settings_scr, name='settings', 
            text=Store.get_text("menu_lang").upper(), icon="translate"
        )
        self.item_lang.bind(on_tab_press=self.clear_search_only)

        self.nav.add_widget(self.item_main)
        self.nav.add_widget(self.item_cart)
        self.nav.add_widget(self.item_profile)
        self.nav.add_widget(self.item_lang)

        return self.nav

    def on_start(self):
        print("[MAIN] APP STARTED. CONNECTING OBSERVERS.")
        Store.add_observer(self.refresh_all_texts)

    def on_cart_tab(self, instance):
        self.clear_search_only(instance)
        if hasattr(self.cart_scr, 'update_data'):
            self.cart_scr.update_data()

    def clear_search_only(self, instance):
        screens_with_header = [self.main_scr, self.catalog_scr, self.product_scr]
        for scr in screens_with_header:
            if hasattr(scr, 'header') and hasattr(scr.header, 'search_field'):
                scr.header.search_field.text = ""

    def refresh_all_texts(self):
        print("[MAIN] REFRESHING UI TEXTS")
        self.item_main.text = Store.get_text("menu_home").upper()
        self.item_cart.text = Store.get_text("menu_cart").upper()
        self.item_profile.text = Store.get_text("menu_profile").upper()
        self.item_lang.text = Store.get_text("menu_lang").upper()
        
        screens = [
            self.main_scr, self.catalog_scr, self.product_scr, 
            self.cart_scr, self.profile_scr, self.settings_scr
        ]
        for scr in screens:
            try:
                if hasattr(scr, 'render_main'): scr.render_main()
                elif hasattr(scr, 'render_settings'): scr.render_settings()
                elif hasattr(scr, 'render_profile'): scr.render_profile()
                if hasattr(scr, 'update_data'): scr.update_data()
            except Exception as e:
                print(f"[MAIN] ERROR REFRESHING SCREEN {scr.name}: {e}")

if __name__ == '__main__':
    MainApp().run()