"""Fixture centre with synchronized competition and matchday selectors."""
from __future__ import annotations
import flet as ft
from src.ui import theme
from src.data import queries
from src.ui.widgets.nav_bar import build_nav_bar
from src.ui.widgets.cards import empty_state
from src.utils.localization import t, display_home_name, display_away_name


def build_fixtures_screen(page):
    from src.ui.app import app_state
    page.navigation_bar = build_nav_bar(page, 3)
    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(rtl=theme.rtl(), controls=[ft.Text(t("no_game_loaded"), rtl=theme.rtl())])
    conn, gs = app_state.db_conn, app_state.game_state
    page._comp_view = getattr(page, "_comp_view", "league")
    all_mds = queries.get_all_matchdays(conn)
    results = ft.Column(rtl=theme.rtl(), spacing=10)
    selector = ft.Dropdown(border_radius=10, border_color=theme.GOLD_BORDER, focused_border_color=theme.ACCENT, filled=True, fill_color=theme.BG_MID, rtl=theme.rtl(), label=t("matchday"), expand=True)
    buttons = []

    def refresh(reset=False):
        cup = page._comp_view == "cup"
        mds = [md for md in all_mds if (md == 0 if cup else md > 0)]
        current = queries.get_current_matchday(conn)
        selected = int(selector.value) if selector.value and not reset else current
        if selected not in mds:
            selected = mds[0] if mds else 0 if cup else 1
        selector.options = [ft.dropdown.Option(str(md), text=t("cup") if md == 0 else f"{t('matchday')} {md}") for md in mds]
        selector.value = str(selected)
        selector.visible = not cup and bool(mds)
        for i, button in enumerate(buttons):
            button.style = theme.tab_style((i == 1) == cup)
        results.controls.clear()
        _populate_results(conn, gs, selected, results)

    def switch(comp):
        def handler(e):
            page._comp_view = comp
            refresh(True)
            page.update()
        return handler
    for comp in ("league", "cup"):
        buttons.append(ft.TextButton(t(comp), rtl=theme.rtl(), expand=True, height=44, on_click=switch(comp)))
    def select(e):
        refresh()
        page.update()
    selector.on_select = select
    refresh(True)
    return ft.Column(rtl=theme.rtl(), expand=True, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(rtl=theme.rtl(), padding=theme.PAGE_PADDING, content=ft.Column(rtl=theme.rtl(), spacing=24, controls=[
            theme.header_bar(t("fixture_results"), subtitle=f"{gs.season_year} / {gs.season_year+1}", page=page, back_route="/table"),
            ft.Container(rtl=theme.rtl(), padding=4, bgcolor=theme.BG_MID, border_radius=12,
                content=ft.Row(rtl=theme.rtl(), spacing=4, controls=buttons)),
            selector, results,
        ]))])


def _populate_results(conn, gs, matchday, column):
    fixtures = queries.get_fixtures_by_matchday(conn, matchday)
    if not fixtures:
        column.controls.append(empty_state(ft.Icons.EVENT_NOTE, t("no_fixtures_matchday")))
        return
    completed = sum(f.played for f in fixtures)
    column.controls.append(ft.Text(f"{t('completed_matches')}: {completed} / {len(fixtures)}", rtl=theme.rtl(), size=12, color=theme.TEXT_MUTED))
    for f in fixtures:
        mine = gs.user_club_id in (f.home_club_id, f.away_club_id)
        result = f.result
        def team(name, managed):
            return ft.Text(name, rtl=theme.rtl(), expand=True, size=14,
                weight=ft.FontWeight.W_600 if managed else ft.FontWeight.NORMAL,
                color=theme.ACCENT if managed else theme.TEXT_PRIMARY,
                max_lines=2, text_align=ft.TextAlign.CENTER)
        score = theme.scoreline(result.home_goals, result.away_goals) if result else t("versus_short")
        column.controls.append(ft.Container(rtl=theme.rtl(), padding=16, border_radius=12,
            bgcolor=theme.CARD_GLASS_STRONG if mine else theme.BG_MID,
            border=ft.border.all(1, theme.ACCENT if mine else theme.GOLD_BORDER),
            content=ft.Column(rtl=theme.rtl(), spacing=12, controls=[
                ft.Text(t("full_time") if result else (f.date.strftime("%d / %m / %Y") if f.date else t("upcoming")), rtl=theme.rtl(), size=11, color=theme.TEXT_MUTED),
                ft.Row(rtl=theme.rtl(), spacing=12, controls=[
                    team(display_home_name(f), f.home_club_id == gs.user_club_id),
                    ft.Text(score, rtl=False, size=26 if result else 12, font_family=theme.display_font(), color=theme.TEXT_PRIMARY),
                    team(display_away_name(f), f.away_club_id == gs.user_club_id),
                ])])))
