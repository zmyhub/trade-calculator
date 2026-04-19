from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty
import csv
import json
import os
import sys
from math import log

# ------------------- 全局基础配置（延迟到 App.build 时执行）-------------------

# 中文字体绑定（解决乱码）— 尝试注册，不在乎平台
from kivy.core.text import LabelBase
import os

FONT_REGISTERED = False
FONT_NAME = "Roboto"

# 尝试多个常见中文字体路径
FONT_PATHS = [
    "/system/fonts/NotoSansCJK-Regular.ttc",
    "/system/fonts/NotoSansSC-Regular.ttf",
    "/system/fonts/NotoSansCJKsc-Regular.ttc",
    "/system/fonts/DroidSansFallbackFull.ttf",
    "/system/fonts/WenQuanYiMicroHei.ttf",
]
for _fp in FONT_PATHS:
    if os.path.exists(_fp):
        try:
            LabelBase.register(name="NotoSans", fn_regular=_fp)
            FONT_REGISTERED = True
            FONT_NAME = "NotoSans"
            break
        except Exception:
            pass

# ------------------- 全局样式类（统一高度+内边距，解决视觉错位） -------------------
class Style:
    bg_main = (0.08, 0.10, 0.15, 1)
    bg_card = (0.15, 0.18, 0.24, 1)
    bg_warn = (0.8, 0.2, 0.2, 1)
    text_white = (0.95, 0.96, 0.98, 1)
    text_gray = (0.65, 0.68, 0.72, 1)
    btn_blue = (0.20, 0.55, 0.92, 1)
    btn_red = (0.90, 0.30, 0.35, 1)
    btn_gray = (0.25, 0.28, 0.34, 1)
    line_blue = (0.20, 0.55, 0.92, 1)
    # 【核心修改】统一所有输入框/Spinner的高度+内边距
    control_height = "48dp"  # 统一高度，确保所有控件在同一水平线
    padding_center = [8, 16, 8, 16]  # 上下内边距16，保证文字垂直居中
    long_press_time = 5

# ------------------- 自定义记录行：支持长按5秒删除 -------------------
class RecordRow(BoxLayout):
    record_data = ObjectProperty(None)
    parent_ref = ObjectProperty(None)
    press_start = NumericProperty(0)
    is_pressing = BooleanProperty(False)

    def __init__(self, record, parent_ref, **kwargs):
        super().__init__(** kwargs)
        self.orientation = "horizontal"
        self.size_hint = (1, None)
        self.height = 40
        self.spacing = 6
        self.record_data = record
        self.parent_ref = parent_ref
        self.press_clock = None

        self.add_widget(FullCenteredLabel(text=str(record.get("id", "")), font_size="14sp", size_hint=(0.1, 1)))
        self.add_widget(FullCenteredLabel(text=str(record.get("symbol", "")), font_size="14sp", size_hint=(0.2, 1)))
        self.add_widget(FullCenteredLabel(text=str(record.get("side", "")), font_size="14sp", size_hint=(0.15, 1)))
        self.add_widget(FullCenteredLabel(text=str(record.get("profit", "")), font_size="14sp", size_hint=(0.15, 1)))
        self.add_widget(FullCenteredLabel(text=str(record.get("balance", "")), font_size="14sp", size_hint=(0.2, 1)))
        self.add_widget(FullCenteredLabel(text=str(record.get("roll_times", 0.00)), font_size="14sp", size_hint=(0.2, 1)))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.is_pressing:
            self.press_start = Clock.time()
            self.is_pressing = True
            self.press_clock = Clock.schedule_interval(self.check_long_press, 0.1)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.is_pressing and self.press_clock:
            self.press_clock.cancel()
            self.press_clock = None
            self.is_pressing = False
            self.press_start = 0
        return super().on_touch_up(touch)
    
    def on_touch_move(self, touch):
        if self.is_pressing and self.press_clock and not self.collide_point(*touch.pos):
            self.press_clock.cancel()
            self.press_clock = None
            self.is_pressing = False
            self.press_start = 0
        return super().on_touch_move(touch)

    def check_long_press(self, dt):
        if self.is_pressing and (Clock.time() - self.press_start >= Style.long_press_time):
            self.press_clock.cancel()
            self.press_clock = None
            self.is_pressing = False
            self.press_start = 0
            self.parent_ref.show_delete_confirm(self.record_data)

# ------------------- 核心控件：统一高度+背景色，解决视觉错位 -------------------
class FullCenteredLabel(Label):
    def __init__(self, text="", **kwargs):
        super().__init__(
            text=text,
            color=Style.text_white,
            font_name=FONT_NAME,
            halign="center",
            valign="center",
            **kwargs
        )
        self.bind(size=self.setter('text_size'))

class FullCenteredBtn(Button):
    def __init__(self, text="", **kwargs):
        super().__init__(
            text=text,
            font_name=FONT_NAME,
            halign="center",
            valign="center",
            border=(0, 0, 0, 0),
            **kwargs
        )
        self.bind(size=self.setter('text_size'))

# 输入框：固定高度，和Spinner统一
class CenterInput(TextInput):
    def __init__(self, hint_text="", text="", **kwargs):
        super().__init__(
            text=text,
            hint_text=hint_text,
            hint_text_color=Style.text_gray,
            font_name=FONT_NAME,
            halign="center",
            padding=Style.padding_center,
            background_color=Style.bg_card,
            foreground_color=Style.text_white,
            cursor_color=Style.text_white,
            height=Style.control_height,  # 固定高度，和Spinner/按钮一致
            **kwargs
        )

# Spinner：修复背景色+固定高度，和输入框/按钮完全对齐
class CenterSpinner(Spinner):
    def __init__(self, text="", values=(), **kwargs):
        super().__init__(
            text=text,
            values=values,
            font_name=FONT_NAME,
            halign="center",
            padding=Style.padding_center,
            background_color=Style.bg_card,  # 【核心修改】Spinner背景色和输入框一致，不再纯黑
            color=Style.text_white,
            height=Style.control_height,  # 固定高度，和输入框/按钮一致
            **kwargs
        )

# ------------------- 自定义专属按钮：固定高度，和输入框/Spinner对齐 -------------------
class MenuBtn(FullCenteredBtn):
    def __init__(self, **kwargs):
        super().__init__(
            text="菜单",
            font_size="16sp",
            background_color=Style.bg_card,
            color=Style.text_white,
            size_hint=(0.15, 1),
            **kwargs
        )

class SubmitBtn(FullCenteredBtn):
    def __init__(self, **kwargs):
        super().__init__(
            text="记录",
            font_size="16sp",
            bold=True,
            background_color=Style.btn_blue,
            color=Style.text_white,
            height=Style.control_height,  # 固定高度，和输入框/Spinner对齐
            **kwargs
        )

class ExportBtn(FullCenteredBtn):
    def __init__(self, **kwargs):
        super().__init__(
            text="导出记录CSV",
            font_size="16sp",
            background_color=Style.btn_blue,
            color=Style.text_white,
            **kwargs
        )

class ClearBtn(FullCenteredBtn):
    def __init__(self, **kwargs):
        super().__init__(
            text="清空所有数据",
            font_size="16sp",
            background_color=Style.btn_red,
            color=Style.text_white,
            **kwargs
        )

class CloseBtn(FullCenteredBtn):
    def __init__(self, **kwargs):
        super().__init__(
            font_size="16sp",
            background_color=Style.btn_gray,
            color=Style.text_white,
            **kwargs
        )

class DeleteBtn(FullCenteredBtn):
    def __init__(self, **kwargs):
        super().__init__(
            text="确认删除",
            font_size="16sp",
            bold=True,
            background_color=Style.bg_warn,
            color=Style.text_white,
            **kwargs
        )

# ------------------- 主界面核心类：控件统一高度+背景色，视觉完全整齐 -------------------
class TradeApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 16
        self.spacing = 10

        # Android 存储路径：优先应用私有目录，桌面用当前目录
        if sys.platform == "android":
            from android.storage import app_storage_path
            base_dir = app_storage_path()
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else '.'

        self.history_file = os.path.join(base_dir, "trade_history.csv")
        self.config_file = os.path.join(base_dir, "trade_config.json")
        self.trade_history = []

        self.load_config()
        self._build_ui()
        self.load_history()

    def _build_ui(self):
        # 1. 顶部标题栏（标题已居中）
        top_bar = BoxLayout(size_hint=(1, 0.08), spacing=10)
        self.menu_btn = MenuBtn()
        self.menu_btn.bind(on_press=self.show_menu)
        top_bar.add_widget(self.menu_btn)
        
        title_layout = BoxLayout(size_hint=(0.7, 1))
        title_layout.add_widget(FullCenteredLabel(
            text="合约滚仓计算器",
            font_size="20sp",
            bold=True,
            size_hint=(1, 1)
        ))
        top_bar.add_widget(title_layout)
        
        right_spacer = BoxLayout(size_hint=(0.15, 1))
        top_bar.add_widget(right_spacer)
        self.add_widget(top_bar)

        # 2. 本金+杠杆滚仓配置行
        config_row = BoxLayout(size_hint=(1, 0.08), spacing=8)
        self.principal = CenterInput(
            hint_text="初始本金 (USDT)",
            text=str(self.config.get("principal", "")),
            font_size="16sp",
            size_hint=(0.5, 1)
        )
        self.rate = CenterInput(
            hint_text="n倍杠杆滚仓n%",
            text=str(self.config.get("rate", "3")),
            font_size="16sp",
            size_hint=(0.5, 1)
        )
        config_row.add_widget(self.principal)
        config_row.add_widget(self.rate)
        self.add_widget(config_row)

        # 3. 核心交易数据输入行（【核心修改】所有控件高度统一，Spinner背景色和输入框一致）
        input_row = BoxLayout(size_hint=(1, None), height=Style.control_height, spacing=6)
        self.symbol = CenterInput(hint_text="币对", font_size="16sp", size_hint=(0.2, 1))
        self.side = CenterSpinner(text="Short", values=("Long", "Short"), font_size="16sp", size_hint=(0.15, 1))
        self.profit = CenterInput(hint_text="盈亏", font_size="16sp", size_hint=(0.15, 1))
        self.balance = CenterInput(hint_text="余额", font_size="16sp", size_hint=(0.2, 1))
        self.submit_btn = SubmitBtn(size_hint=(0.3, 1))
        self.submit_btn.bind(on_press=self.add_record)
        input_row.add_widget(self.symbol)
        input_row.add_widget(self.side)
        input_row.add_widget(self.profit)
        input_row.add_widget(self.balance)
        input_row.add_widget(self.submit_btn)
        self.add_widget(input_row)

        # 4. 表格表头
        header_row = BoxLayout(size_hint=(1, 0.06), spacing=6)
        header_row.add_widget(FullCenteredLabel("序号", font_size="14sp", size_hint=(0.1, 1)))
        header_row.add_widget(FullCenteredLabel("币对", font_size="14sp", size_hint=(0.2, 1)))
        header_row.add_widget(FullCenteredLabel("方向", font_size="14sp", size_hint=(0.15, 1)))
        header_row.add_widget(FullCenteredLabel("盈亏", font_size="14sp", size_hint=(0.15, 1)))
        header_row.add_widget(FullCenteredLabel("余额", font_size="14sp", size_hint=(0.2, 1)))
        header_row.add_widget(FullCenteredLabel("滚仓次数", font_size="14sp", size_hint=(0.2, 1)))
        self.add_widget(header_row)

        # 5. 可滑动历史记录列表
        scroll_view = ScrollView(size_hint=(1, 1))
        self.record_container = BoxLayout(orientation='vertical', spacing=4, size_hint_y=None)
        self.record_container.bind(minimum_height=self.record_container.setter('height'))
        scroll_view.add_widget(self.record_container)
        self.add_widget(scroll_view)

    # 删除确认弹窗
    def show_delete_confirm(self, record):
        content = BoxLayout(orientation='vertical', spacing=20, padding=30)
        content.add_widget(FullCenteredLabel(
            text=f"确认删除这条记录？\n序号：{record.get('id', '')} | 币对：{record.get('symbol', '未知')}",
            font_size="16sp"
        ))
        btn_row = BoxLayout(orientation='horizontal', spacing=15, size_hint=(1, 0.3))
        cancel_btn = CloseBtn(text="取消", size_hint=(0.5, 1))
        delete_btn = DeleteBtn(size_hint=(0.5, 1))
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(delete_btn)
        content.add_widget(btn_row)

        self.delete_popup = Popup(
            title="删除确认",
            title_font=FONT_NAME,
            title_size="18sp",
            title_color=Style.text_white,
            content=content,
            size_hint=(0.8, 0.4),
            background_color=Style.bg_main,
            separator_color=Style.line_blue,
            auto_dismiss=False
        )
        cancel_btn.bind(on_press=lambda x: self.delete_popup.dismiss())
        delete_btn.bind(on_press=lambda x: self.delete_record(record))
        self.delete_popup.open()

    # 执行删除记录
    def delete_record(self, record):
        self.delete_popup.dismiss()
        self.trade_history = [r for r in self.trade_history if r.get('id') != record.get('id')]
        for idx, r in enumerate(self.trade_history):
            r['id'] = str(idx + 1)
        self.record_container.clear_widgets()
        for r in self.trade_history:
            self.render_record(r)
        self.save_history()

    # 配置加载/保存
    def load_config(self):
        self.config = {"principal": "", "rate": "3"}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except:
                pass

    def save_config(self):
        try:
            data = {
                "principal": self.principal.text.strip(),
                "rate": self.rate.text.strip() or "3"
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            self.config = data
        except:
            pass

    # 复利滚仓次数计算
    def calc_roll_times(self, balance):
        try:
            principal = float(self.config.get("principal", 0))
            rate = float(self.config.get("rate", 3)) / 100
            balance = float(balance)
            if principal <= 0 or rate <= 0 or balance < principal:
                return 0.00
            return round(log(balance / principal) / log(1 + rate), 2)
        except:
            return 0.00

    # 新增记录
    def add_record(self, instance):
        try:
            self.save_config()
            symbol = self.symbol.text.strip() or "未知"
            side = self.side.text
            profit = self.profit.text.strip() or "0"
            balance = self.balance.text.strip()
            roll_times = self.calc_roll_times(balance)
            record = {
                "id": str(len(self.trade_history) + 1),
                "symbol": symbol,
                "side": side,
                "profit": profit,
                "balance": balance,
                "roll_times": roll_times
            }
            self.trade_history.append(record)
            self.save_history()
            self.render_record(record)
            self.symbol.text = ""
            self.profit.text = ""
            self.balance.text = ""
        except:
            pass

    # 保存/加载历史记录
    def save_history(self):
        try:
            fieldnames = ["id", "symbol", "side", "profit", "balance", "roll_times"]
            with open(self.history_file, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.trade_history)
        except:
            pass

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8-sig") as f:
                    self.trade_history = list(csv.DictReader(f))
                self.record_container.clear_widgets()
                for record in self.trade_history:
                    self.render_record(record)
            except:
                self.trade_history = []

    # 渲染记录行
    def render_record(self, record):
        try:
            self.record_container.add_widget(RecordRow(record, self))
        except:
            pass

    # 菜单弹窗（Popup 版本，稳定）
    def show_menu(self, instance):
        content = BoxLayout(orientation='vertical', spacing=12, padding=20)
        export_btn = ExportBtn(size_hint=(1, 0.3))
        clear_btn = ClearBtn(size_hint=(1, 0.3))
        close_btn = CloseBtn(text="关闭", size_hint=(1, 0.3))
        content.add_widget(export_btn)
        content.add_widget(clear_btn)
        content.add_widget(close_btn)
        popup = Popup(
            title="功能菜单",
            title_font=FONT_NAME,
            title_size="20sp",
            title_color=Style.text_white,
            content=content,
            size_hint=(0.8, 0.6),
            background_color=Style.bg_main,
            separator_color=Style.line_blue,
            auto_dismiss=False
        )
        export_btn.bind(on_press=lambda x: self._do_export())
        clear_btn.bind(on_press=lambda x: self._do_clear())
        close_btn.bind(on_press=lambda x, p=popup: p.dismiss())
        popup.open()

    # ---- Android Toast 工具 ----
    def _show_toast(self, msg, long_duration=False):
        """在 Android 上显示 Toast，在桌面/其他平台打印到 stdout"""
        try:
            from jnius import autoclass
            from android.runnable import run_on_ui_thread
            Toast = autoclass('android.widget.Toast')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            duration = Toast.LENGTH_LONG if long_duration else Toast.LENGTH_SHORT

            @run_on_ui_thread
            def show_toast():
                Toast.makeText(PythonActivity.mActivity, msg, duration).show()
            show_toast()
        except Exception:
            # 非 Android 平台降级到打印
            print(f"[toast] {msg}")

    def _do_export(self):
        """导出 CSV 到 Downloads 文件夹（通过 MediaStore API，Android 10+ 有效）"""
        import traceback, time, shutil

        debug_file = os.path.join(os.path.dirname(self.history_file), "export_debug.log")

        try:
            self.save_history()
            history_count = len(self.trade_history)

            if history_count == 0:
                self._show_toast("无记录可导出", long_duration=True)
                return

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            file_name = f"trade_history_{timestamp}.csv"

            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(f"[{timestamp}] export start, records={history_count}\n")

            # 通过 jnius 调用 Android MediaStore API
            from jnius import autoclass

            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()

            ContentValues = autoclass('android.content.ContentValues')
            MediaStoreDownloads = autoclass('android.provider.MediaStore$Downloads')
            Environment = autoclass('android.os.Environment')
            Build = autoclass('android.os.Build')

            values = ContentValues()
            values.put("_display_name", file_name)
            values.put("mime_type", "text/csv")

            if Build.VERSION.SDK_INT >= 29:
                # Android 10+：必须用 MediaStore API
                values.put("relative_path", "Download")
            else:
                # Android 9 及以下
                downloads_dir = Environment.getExternalStoragePublicDirectory("downloads").getAbsolutePath()
                values.put("_data", f"{downloads_dir}/{file_name}")

            uri = resolver.insert(MediaStoreDownloads.EXTERNAL_CONTENT_URI, values)

            with resolver.openOutputStream(uri) as out:
                with open(self.history_file, "rb") as src:
                    shutil.copyfileobj(src, out)

            with open(debug_file, "a", encoding="utf-8") as f:
                f.write(f"SUCCESS: {file_name}\n")

            self._show_toast(f"已保存到:\nDownload/{file_name}", long_duration=True)

        except Exception as e:
            err = traceback.format_exc()
            try:
                with open(debug_file, "a", encoding="utf-8") as f:
                    f.write(f"ERROR: {e}\n{err}\n")
            except:
                pass
            try:
                self._show_toast(f"导出失败: {e}", long_duration=True)
            except:
                pass

    def _dismiss_toast(self, *l):
        if hasattr(self, "_toast_label") and self._toast_label.parent:
            self.root.remove_widget(self._toast_label)

    def _do_clear(self):
        """清空所有数据"""
        self.trade_history = []
        self.record_container.clear_widgets()
        self.config = {"principal": "", "rate": "3"}
        if os.path.exists(self.history_file):
            os.remove(self.history_file)
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        self.principal.text = ""
        self.rate.text = "3"
        self.symbol.text = ""
        self.profit.text = ""
        self.balance.text = ""
        try:
            from jnius import autoclass
            from android.runnable import run_on_ui_thread
            Toast = autoclass('android.widget.Toast')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            @run_on_ui_thread
            def show_toast():
                Toast.makeText(PythonActivity.mActivity, "已清空", Toast.LENGTH_SHORT).show()
            show_toast()
        except Exception:
            pass

# ------------------- 应用启动类 -------------------
class TradeRecorderApp(App):
    def build(self):
        from kivy.core.window import Window
        Window.clearcolor = (0.08, 0.10, 0.15, 1)
        Window.softinput_mode = "below_target"
        return TradeApp()

# ------------------- 主入口 -------------------
if __name__ == "__main__":
    TradeRecorderApp().run()
