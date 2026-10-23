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
    def style(selected):
        return ft.ButtonStyle(
            color=theme.TEXT_PRIMARY if selected else theme.TEXT_MUTED,
            bgcolor=theme.BG_SURFACE if selected else ft.Colors.TRANSPARENT,
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.padding.symmetric(horizontal=10, vertical=12))
    for i, label in enumerate(labels):
        sections[i].visible = i == 0
        buttons.append(ft.TextButton(label, expand=True, height=44,
                                    style=style(i == 0), on_click=choose(i)))
    return ft.Container(padding=4, border_radius=12, bgcolor=theme.BG_DARK,
                        content=ft.Row(spacing=2, rtl=is_rtl(), controls=buttons))


def metric(label, value, color=None):
    return ft.Container(expand=True, padding=12, border_radius=10, bgcolor=theme.BG_SURFACE,
        content=ft.Column(spacing=6, controls=[
            ft.Text(str(value), size=28, font_family=theme.display_font(),
                    color=color or theme.TEXT_PRIMARY),
            ft.Text(label, size=11, color=theme.TEXT_MUTED),
        ]))


def section_title(text):
    return ft.Container(padding=ft.padding.only(top=10, bottom=4),
        content=ft.Text(text, size=15, weight=ft.FontWeight.W_600, color=theme.TEXT_PRIMARY))
