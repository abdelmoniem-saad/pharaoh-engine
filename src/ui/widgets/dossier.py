"""Shared dossier components; navigation changes only presentation state."""
import flet as ft
from src.ui import theme


def section_tabs(page, labels, sections):
    from src.utils.localization import is_rtl
    buttons = []
    def choose(index):
        def handler(e):
            for i, section in enumerate(sections):
                section.visible = i == index
                buttons[i].style = style(i == index)
            page.update()
        return handler
    style = theme.tab_style
    for i, label in enumerate(labels):
        sections[i].visible = i == 0
        buttons.append(ft.TextButton(label, rtl=theme.rtl(), expand=True, height=44,
                                    style=style(i == 0), on_click=choose(i)))
    return ft.Container(rtl=theme.rtl(), padding=4, border_radius=12, bgcolor=theme.BG_DARK,
                        content=ft.Row(spacing=2, rtl=is_rtl(), controls=buttons))


def metric(label, value, color=None):
    return ft.Container(rtl=theme.rtl(), expand=True, padding=12, border_radius=10, bgcolor=theme.BG_SURFACE,
        content=ft.Column(rtl=theme.rtl(), spacing=6, controls=[
            ft.Text(str(value), rtl=theme.rtl(), size=28, font_family=theme.display_font(),
                    color=color or theme.TEXT_PRIMARY),
            ft.Text(label, rtl=theme.rtl(), size=11, color=theme.TEXT_MUTED),
        ]))


def section_title(text):
    return ft.Container(rtl=theme.rtl(), padding=ft.padding.only(top=10, bottom=4),
        content=ft.Text(text, rtl=theme.rtl(), size=15, weight=ft.FontWeight.W_600, color=theme.TEXT_PRIMARY))
