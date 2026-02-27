"""
Inbox screen — game messages and news feed.
"""
from __future__ import annotations
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.app import App
from src.data import queries


class InboxScreen(Screen):
    """Display in-game messages — match reports, news, board updates."""

    def on_enter(self):
        self.clear_widgets()
        app = App.get_running_app()
        if not app.db_conn or not app.game_state:
            self.add_widget(Label(text="No game loaded"))
            return

        conn = app.db_conn
        messages = queries.get_inbox(conn, limit=30)

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(5))
        layout.add_widget(Label(
            text="Inbox", font_size=dp(20), bold=True,
            size_hint_y=None, height=dp(40),
        ))

        if not messages:
            layout.add_widget(Label(text="No messages yet.", font_size=dp(14)))
        else:
            scroll = ScrollView(size_hint=(1, 1))
            msg_list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
            msg_list.bind(minimum_height=msg_list.setter("height"))

            for msg in messages:
                read_indicator = "" if msg.is_read else "[NEW] "
                cat_icon = {"match": "⚽", "media": "📰", "board": "🏛️",
                            "transfer": "💰"}.get(msg.category, "📧")

                btn = Button(
                    text=f"{cat_icon} {read_indicator}{msg.subject}\n{msg.date.strftime('%d %b')} — {msg.body[:60]}...",
                    size_hint_y=None, height=dp(60), font_size=dp(11),
                    halign="left", text_size=(dp(350), None),
                )
                btn.msg_id = msg.id
                btn.bind(on_press=lambda inst: self._mark_read(conn, inst.msg_id))
                msg_list.add_widget(btn)

            scroll.add_widget(msg_list)
            layout.add_widget(scroll)

        nav = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
        for target, text in [("squad", "Squad"), ("match_day", "Match"), ("table", "Table")]:
            btn = Button(text=text, font_size=dp(13))
            btn.screen_target = target
            btn.bind(on_press=lambda inst: setattr(self.manager, 'current', inst.screen_target))
            nav.add_widget(btn)
        layout.add_widget(nav)
        self.add_widget(layout)

    def _mark_read(self, conn, msg_id):
        queries.mark_message_read(conn, msg_id)
        self.on_enter()

