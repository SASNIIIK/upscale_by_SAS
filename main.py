import os
import cv2
import numpy as np

# Настройка Kivy перед импортом остальных модулей
from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'system')

from kivy.lang import Builder
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast

# Запрашиваем разрешения для Android при старте
if platform == "android":
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE
    ])

# Интерфейс приложения на языке KV (Бело-оливковые тона)
KV = '''
MDScreen:
    md_bg_color: 0.98, 0.98, 0.95, 1  # Светло-кремовый/белый фон

    MDBoxLayout:
        orientation: 'vertical'
        spacing: "20dp"
        padding: "24dp"

        # Шапка приложения
        MDLabel:
            text: "Fast Color Image Upscaler"
            halign: "center"
            font_style: "H5"
            bold: True
            theme_text_color: "Custom"
            text_color: 0.28, 0.35, 0.24, 1  # Темно-оливковый акцент
            size_hint_y: None
            height: "40dp"

        # Карточка для отображения статуса/превью
        MDCard:
            orientation: "vertical"
            padding: "16dp"
            size_hint: 1, 0.6
            md_bg_color: 1, 1, 1, 1
            elevation: 1
            radius: [16, 16, 16, 16]
            
            MDBoxLayout:
                orientation: "vertical"
                spacing: "10dp"

                # Место под превью картинки
                FitImage:
                    id: image_preview
                    source: ""
                    allow_stretch: True
                    keep_ratio: True
                    size_hint: (1, 0.8) if self.source else (1, 0.001)
                    opacity: 1 if self.source else 0

                # Текстовое поле состояния
                MDLabel:
                    id: status_label
                    text: "Выберите цветное изображение для увеличения"
                    halign: "center"
                    theme_text_color: "Secondary"
                    font_style: "Body1"

        # Кнопки управления
        MDBoxLayout:
            orientation: 'horizontal'
            spacing: "16dp"
            size_hint_y: None
            height: "56dp"

            MDRaisedButton:
                text: "Выбрать файл"
                size_hint_x: 0.5
                height: "56dp"
                md_bg_color: 0.43, 0.52, 0.38, 1  # Оливковый цвет
                text_color: 1, 1, 1, 1
                on_release: app.open_file_manager()

            MDRaisedButton:
                id: process_btn
                text: "Увеличить"
                size_hint_x: 0.5
                height: "56dp"
                md_bg_color: 0.28, 0.35, 0.24, 1  # Темно-оливковый цвет
                text_color: 1, 1, 1, 1
                disabled: True
                on_release: app.process_image()
'''

class UpscaleApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_manager = None
        self.selected_path = None

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Olive"
        
        self.file_manager = MDFileManager(
            exit_manager=self.close_file_manager,
            select_path=self.select_path,
            preview=True
        )
        return Builder.load_string(KV)

    def open_file_manager(self):
        if platform == "android":
            from android.storage import primary_external_storage_path
            path = primary_external_storage_path()
        else:
            path = os.path.expanduser("~")
            
        self.file_manager.show(path)

    def select_path(self, path):
        if path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            self.selected_path = path
            self.root.ids.image_preview.source = path
            self.root.ids.status_label.text = f"Выбран файл:\n{os.path.basename(path)}"
            self.root.ids.process_btn.disabled = False
        else:
            toast("Пожалуйста, выберите изображение (.jpg, .png)")
        self.close_file_manager()

    def close_file_manager(self, *args):
        self.file_manager.close()

    def process_image(self):
        if not self.selected_path:
            return

        try:
            self.root.ids.status_label.text = "Обработка цвета..."
            
            dir_name = os.path.dirname(self.selected_path)
            file_name = os.path.basename(self.selected_path)
            name, ext = os.path.splitext(file_name)
            output_path = os.path.join(dir_name, f"{name}_upscaled_color{ext}")

            # Запуск оптимизированного цветного алгоритма
            self.upscale_image_colors(self.selected_path, output_path)

            self.root.ids.status_label.text = f"Готово!\nНовое разрешение x2\nСохранено рядом с оригиналом."
            toast("Изображение успешно увеличено!")
            
            self.root.ids.image_preview.source = output_path
            self.root.ids.image_preview.reload()
            
        except Exception as e:
            self.root.ids.status_label.text = "Ошибка обработки изображения"
            toast(f"Ошибка: {str(e)}")

    def upscale_image_colors(self, image_path, output_path):
        # Оптимизированный цветной алгоритм без использования scipy (через cv2.filter2D)
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Не удалось найти или загрузить файл")

        h, w, c = img.shape

        upscaled = np.zeros((h * 2, w * 2, c), dtype=np.float32)
        upscaled[::2, ::2] = img

        mask = np.zeros_like(upscaled)
        mask[::2, ::2] = 1.0

        # Ядро свертки (3х3): единицы по краям, в центре 0
        kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.float32)

        # cv2.filter2D делает свертку по всем каналам автоматически. 
        # anchor=(-1,-1) означает центр, а borderType=cv2.BORDER_CONSTANT аналог cval=0 в scipy
        neighbor_sums = cv2.filter2D(upscaled, -1, kernel, anchor=(-1, -1), borderType=cv2.BORDER_CONSTANT)
        neighbor_counts = cv2.filter2D(mask, -1, kernel, anchor=(-1, -1), borderType=cv2.BORDER_CONSTANT)

        neighbor_counts[neighbor_counts == 0] = 1
        interpolated = neighbor_sums / neighbor_counts

        result = np.where(mask == 1, upscaled, interpolated)
        final_image = np.clip(result, 0, 255).astype(np.uint8)

        cv2.imwrite(output_path, final_image)

if __name__ == "__main__":
    UpscaleApp().run()
