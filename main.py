import os
import cv2
import numpy as np

from kivy.lang import Builder
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast

KV = '''
MDScreen:
    md_bg_color: 0.98, 0.98, 0.95, 1

    MDBoxLayout:
        orientation: 'vertical'
        spacing: "20dp"
        padding: "24dp"

        MDLabel:
            text: "Fast Color Image Upscaler"
            halign: "center"
            font_style: "H5"
            bold: True
            theme_text_color: "Custom"
            text_color: 0.28, 0.35, 0.24, 1
            size_hint_y: None
            height: "40dp"

        MDCard:
            orientation: "vertical"
            padding: "16dp"
            size_hint: 1, 0.6
            md_bg_color: 1, 1, 1, 1
            elevation: 1
            radius: 16

            MDBoxLayout:
                orientation: "vertical"
                spacing: "10dp"

                FitImage:
                    id: image_preview
                    source: ""
                    allow_stretch: True
                    keep_ratio: True
                    size_hint: (1, 0.8) if self.source else (1, 0.001)
                    opacity: 1 if self.source else 0

                MDLabel:
                    id: status_label
                    text: "Выберите цветное изображение для увеличения"
                    halign: "center"
                    theme_text_color: "Secondary"
                    font_style: "Body1"

        MDBoxLayout:
            orientation: 'horizontal'
            spacing: "16dp"
            size_hint_y: None
            height: "56dp"

            MDRaisedButton:
                text: "Выбрать файл"
                size_hint_x: 0.5
                height: "56dp"
                md_bg_color: 0.43, 0.52, 0.38, 1
                text_color: 1, 1, 1, 1
                on_release: app.open_file_manager()

            MDRaisedButton:
                id: process_btn
                text: "Увеличить"
                size_hint_x: 0.5
                height: "56dp"
                md_bg_color: 0.28, 0.35, 0.24, 1
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
        return Builder.load_string(KV)

    def on_start(self):
        if platform == "android":
            try:
                from android.permissions import request_permissions, Permission
                request_permissions((
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    "android.permission.READ_MEDIA_IMAGES"
                ))
            except Exception as e:
                toast(f"Ошибка прав: {e}")

        self.file_manager = MDFileManager(
            exit_manager=self.close_file_manager,
            select_path=self.select_path,
            preview=False
        )

    def open_file_manager(self):
        if platform == "android":
            try:
                from android.storage import primary_external_storage_path
                path = primary_external_storage_path()
            except Exception:
                path = "/storage/emulated/0"
        else:
            path = os.path.expanduser("~")

        self.file_manager.show(path)

    def select_path(self, path):
        if os.path.isfile(path) and path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            self.selected_path = path
            self.root.ids.image_preview.source = path
            self.root.ids.status_label.text = f"Выбран файл:\n{os.path.basename(path)}"
            self.root.ids.process_btn.disabled = False
        else:
            toast("Пожалуйста, выберите изображение (.jpg, .png)")
        self.close_file_manager()

    def close_file_manager(self, *args):
        if self.file_manager:
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

            self.upscale_image_colors(self.selected_path, output_path)

            self.root.ids.status_label.text = "Готово!\nНовое разрешение x2\nСохранено рядом с оригиналом."
            toast("Изображение успешно увеличено!")

            self.root.ids.image_preview.source = output_path
            self.root.ids.image_preview.reload()

        except Exception as e:
            self.root.ids.status_label.text = f"Ошибка: {str(e)}"
            toast("Сбой при обработке")

    def upscale_image_colors(self, image_path, output_path):
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Не удалось загрузить файл")

        h, w, c = img.shape

        upscaled = np.zeros((h * 2, w * 2, c), dtype=np.float32)
        upscaled[::2, ::2] = img

        mask = np.zeros_like(upscaled)
        mask[::2, ::2] = 1.0

        kernel = np.array(((1, 1, 1), (1, 0, 1), (1, 1, 1)), dtype=np.float32)

        neighbor_sums = cv2.filter2D(upscaled, -1, kernel, anchor=(-1, -1), borderType=cv2.BORDER_CONSTANT)
        neighbor_counts = cv2.filter2D(mask, -1, kernel, anchor=(-1, -1), borderType=cv2.BORDER_CONSTANT)

        neighbor_counts[neighbor_counts == 0] = 1
        interpolated = neighbor_sums / neighbor_counts

        result = np.where(mask == 1, upscaled, interpolated)
        final_image = np.clip(result, 0, 255).astype(np.uint8)

        cv2.imwrite(output_path, final_image)


if __name__ == "__main__":
    UpscaleApp().run()
