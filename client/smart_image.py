import os
from kivy.uix.image import AsyncImage
from kivy.clock import Clock
from store import Store
from kivy.network.urlrequest import UrlRequest

class SmartImage(AsyncImage):
    _loading_count = 0
    _max_loading = 8
    _dead_urls = set()

    def __init__(self, **kwargs):
        self._current_url = ""
        self._local_loading = False
        super().__init__(**kwargs)
        self.mipmap = True

    def on_source(self, instance, value):
        if not hasattr(self, '_local_loading') or not value or self._local_loading:
            return
            
        if value.startswith('http'):
            if value in SmartImage._dead_urls:
                return

            full_url = Store.get_image_url(value)
            img_name = os.path.basename(value)
            local_path = os.path.join(Store.IMG_CACHE_DIR, img_name)
            abs_local = os.path.abspath(local_path)
            
            if os.path.exists(abs_local) and os.path.getsize(abs_local) > 0:
                print(f"[LOG] IMAGE FROM CACHE: {img_name}")
                self._local_loading = True
                self.source = abs_local
                self._local_loading = False
                return

            print(f"[LOG] START DOWNLOAD: {full_url}")
            self._current_url = value
            self.queue_download(full_url, abs_local, value)

    def queue_download(self, url, save_path, original_value):
        if SmartImage._loading_count >= SmartImage._max_loading:
            Clock.schedule_once(lambda dt: self.queue_download(url, save_path, original_value), 0.2)
            return
        
        SmartImage._loading_count += 1
        UrlRequest(
            url, 
            on_success=lambda req, res: self.save_img(original_value, res, save_path),
            on_failure=lambda req, res: self.on_err(original_value),
            on_error=lambda req, res: self.on_err(original_value),
            timeout=15
        )

    def save_img(self, url, result, save_path):
        try:
            with open(save_path, "wb") as f:
                f.write(result)
            if self._current_url == url:
                print(f"[LOG] IMAGE SAVED: {os.path.basename(save_path)}")
                self._local_loading = True
                self.source = os.path.abspath(save_path)
                self._local_loading = False
        except Exception as e:
            print(f"[LOG] SAVE ERROR: {str(e)}")
        finally:
            SmartImage._loading_count -= 1

    def on_err(self, url):
        print(f"[LOG] DOWNLOAD FAILED: {url}")
        SmartImage._dead_urls.add(url)
        SmartImage._loading_count -= 1

    def _on_source_load(self, *args):
        if self._coreimage:
            super()._on_source_load(*args)