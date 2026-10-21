"""
Squad management screen — view players, tap for detailed stats.
"""
from __future__ import annotations

import flet as ft
from src.ui import theme

from src.data import queries
from src.core.player import calculate_overall_rating
from src.ui.widgets.nav_bar import build_nav_bar
from src.ui.widgets.stat_bar import stat_bar
from src.ui.widgets.cards import (
    section_card, info_tile, player_card_h, position_group_header,
    action_card, form_chips, kv_row, collapsible_section,
)
from src.utils.localization import t, t_format, display_name


def build_squad_screen(page: ft.Page) -> ft.Column:
    """Build the squad management content with mobile-friendly card layout."""
    from src.ui.app import app_state, navigate

    page.navigation_bar = build_nav_bar(page, 0)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text(t("no_game_loaded"))])

    conn = app_state.db_conn
    gs = app_state.game_state
    club = queries.get_club(conn, gs.user_club_id)
    if not club:
        return ft.Column(controls=[ft.Text(t("club_not_found"))])

    players = queries.get_players_by_club(conn, club.id)

    # Football order keeps each position group contiguous.
    position_order = {p: i for i, p in enumerate(("GK", "CB", "LB", "RB", "CDM", "CM", "LM", "RM", "CAM", "LW", "RW", "ST"))}
    # Sorting
    sort_options = {
        t("position") + ":": lambda p: (position_order.get(p.position.value, 99), -calculate_overall_rating(p)),
        t("overall") + " ↓": lambda p: -calculate_overall_rating(p),
        t("age"): lambda p: p.age,
        t("fitness"): lambda p: -p.fitness,
        t("form") + " ↓": lambda p: -p.form,
        t("morale"): lambda p: -p.morale,
    }
    default_sort = list(sort_options.keys())[0]
    players.sort(key=sort_options[default_sort])

    # Squad summary
    avg_ovr = sum(calculate_overall_rating(p) for p in players) / max(len(players), 1)
    avg_age = sum(p.age for p in players) / max(len(players), 1)
    injured_count = sum(1 for p in players if p.injury_days_remaining > 0)
    suspended_count = sum(1 for p in players if p.suspension_matches > 0)

    # Build player cards
    def _build_player_list(sorted_players, grouped=True):
        """Build a list of player_card_h widgets, grouped by position."""
        cards = []
        from src.utils.config import POSITION_GROUP_MAP, PositionGroup

        current_group = None
        group_counter = {}

        # Pre-count groups
        for p in sorted_players:
            grp = POSITION_GROUP_MAP.get(p.position, PositionGroup.MIDFIELDER)
            group_counter[grp.value] = group_counter.get(grp.value, 0) + 1

        for player in sorted_players:
            grp = POSITION_GROUP_MAP.get(player.position, PositionGroup.MIDFIELDER)
            if grouped and grp.value != current_group:
                current_group = grp.value
                group_label = {
                    "GK": t("goalkeepers"), "DEF": t("defenders"), "MID": t("midfielders"), "ATT": t("forwards"),
                }.get(current_group, current_group)
                cards.append(position_group_header(
                    group_label, group_counter.get(current_group, 0)
                ))

            ovr = calculate_overall_rating(player)

            def make_click_handler(p=player, o=ovr):
                def handler(e):
                    _show_player_detail(page, p, o)
                return handler

            cards.append(player_card_h(
                name=display_name(player),
                position=player.position.value,
                ovr=ovr,
                age=player.age,
                fitness=player.fitness,
                form=player.form,
                morale=player.morale,
                is_captain=player.is_captain,
                is_injured=player.injury_days_remaining > 0,
                is_suspended=player.suspension_matches > 0,
                transfer_listed=player.transfer_listed,
                training_focus=player.training_focus,
                on_click=make_click_handler(),
            ))
        return cards

    player_cards = _build_player_list(players)

    # The player list container (will be rebuilt on sort)
    player_list_col = ft.Column(spacing=0, controls=player_cards)

    def on_sort_change(e):
        key = e.control.value
        sort_fn = sort_options.get(key, sort_options[default_sort])
        players.sort(key=sort_fn)
        player_list_col.controls = _build_player_list(players, grouped=key == default_sort)
        page.update()

    # Recent form
    recent_fixes = queries.get_user_recent_fixtures(conn, gs.user_club_id, limit=5)
    form_results = []
    for f in recent_fixes:
        if not f.result:
            continue
        is_h = f.home_club_id == gs.user_club_id
        ug = f.result.home_goals if is_h else f.result.away_goals
        og = f.result.away_goals if is_h else f.result.home_goals
        form_results.append("W" if ug > og else "L" if ug < og else "D")

    # League position
    standings = queries.get_standings(conn)
    user_pos = 0
    user_pts = 0
    for i, s in enumerate(standings, 1):
        if s.club_id == gs.user_club_id:
            user_pos = i
            user_pts = s.points
            break

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=ft.padding.all(theme.PAGE_PADDING),
                content=ft.Column(
                    spacing=theme.SECTION_SPACING,
                    controls=[
                        # ── Header (minimal) ────────────────────────────
                        theme.header_bar(
                            title=t("squad"),
                            subtitle=display_name(club) + " · " + gs.current_date.strftime("%d %b %Y"),
                            icon=ft.Icons.SHIELD,
                            page=page,
                            extra_controls=[
                                ft.IconButton(icon=ft.Icons.SAVE_OUTLINED, icon_size=18,
                                              icon_color=theme.TEXT_SECONDARY,
                                              tooltip=t("save"),
                                              on_click=lambda e: _save_game(page, conn, gs)),
                            ],
                        ),

                        # Quick nav
                        ft.Row(spacing=6, controls=[
                            ft.OutlinedButton(t("my_club"), height=44,
                                              on_click=lambda e: navigate(page, "/club"),
                                              style=ft.ButtonStyle(
                                                  padding=ft.padding.symmetric(horizontal=12),
                                                  shape=ft.RoundedRectangleBorder(radius=10),
                                                  side=ft.BorderSide(1, theme.GOLD_BORDER),
                                              )),
                            ft.OutlinedButton(t("transfers"), height=44,
                                              on_click=lambda e: navigate(page, "/transfers"),
                                              style=ft.ButtonStyle(
                                                  padding=ft.padding.symmetric(horizontal=12),
                                                  shape=ft.RoundedRectangleBorder(radius=10),
                                                  side=ft.BorderSide(1, theme.GOLD_BORDER),
                                              )),
                        ]),

                        ft.Row(spacing=12, controls=[
                            _squad_metric(t("squad_label"), str(len(players))),
                            _squad_metric(t("avg_ovr"), f"{avg_ovr:.0f}"),
                            _squad_metric(t("position"), str(user_pos)),
                        ]),

                        # ── Sort + Compare + Player List ────────────────
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(t("players"),
                                        size=theme.CAPTION_SIZE, color=theme.TEXT_SECONDARY, weight=ft.FontWeight.W_600),
                                ft.Row(spacing=4, tight=True, controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.COMPARE_ARROWS, icon_size=18,
                                        icon_color=theme.TEXT_SECONDARY, tooltip=t("compare_players"),
                                        on_click=lambda e: _start_compare(page, players),
                                    ),
                                    ft.Dropdown(
                                        label=t("sort_by"),
                                        value=default_sort,
                                        options=[ft.dropdown.Option(k) for k in sort_options],
                                        on_select=on_sort_change,
                                        width=150, text_size=12,
                                    ),
                                ]),
                            ],
                        ),

                        # ── Player Cards ────────────────────────────────
                        player_list_col,
                    ],
                ),
            ),
        ],
    )


def _squad_metric(label, value):
    return ft.Container(expand=True, padding=16, border_radius=12,
        bgcolor=theme.CARD_GLASS_STRONG,
        content=ft.Column(spacing=8, controls=[
            ft.Text(label, size=11, color=theme.TEXT_MUTED),
            ft.Text(value, size=26, weight=ft.FontWeight.W_600, color=theme.TEXT_PRIMARY),
        ]))


def _show_player_detail(page: ft.Page, player, ovr: int):
    """Show a detailed player profile dialog with all stats."""
    from src.core.player import get_morale_description
    a = player.attributes
    s = player.season_stats

    fit_color = (
        ft.Colors.GREEN_400 if player.fitness >= 80
        else ft.Colors.YELLOW_400 if player.fitness >= 50
        else ft.Colors.RED_400
    )
    morale_desc = get_morale_description(player)
    morale_color = (
        ft.Colors.GREEN_400 if player.morale >= 70
        else theme.GOLD if player.morale >= 40
        else ft.Colors.RED_400
    )

    # Injury/suspension status
    status_badges = []
    if player.injury_days_remaining > 0:
        status_badges.append(
            ft.Container(
                content=ft.Text(f"🏥 Injured: {player.injury_type} ({player.injury_days_remaining}d)",
                                size=11, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_800,
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border_radius=6,
            )
        )
    if player.suspension_matches > 0:
        status_badges.append(
            ft.Container(
                content=ft.Text(f"🚫 Suspended: {player.suspension_matches} match(es)",
                                size=11, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.ORANGE_800,
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border_radius=6,
            )
        )

    # Technical stats
    tech_stats = [
        stat_bar("Finishing", a.finishing),
        stat_bar("Passing", a.passing),
        stat_bar("Dribbling", a.dribbling),
        stat_bar("First Touch", a.first_touch),
        stat_bar("Crossing", a.crossing),
        stat_bar("Heading", a.heading),
        stat_bar("Long Shots", a.long_shots),
    ]

    # Physical stats
    phys_stats = [
        stat_bar("Pace", a.pace),
        stat_bar("Stamina", a.stamina),
        stat_bar("Strength", a.strength),
        stat_bar("Agility", a.agility),
        stat_bar("Jumping", a.jumping),
    ]

    # Mental stats
    mental_stats = [
        stat_bar("Composure", a.composure),
        stat_bar("Vision", a.vision),
        stat_bar("Work Rate", a.work_rate),
        stat_bar("Positioning", a.positioning),
        stat_bar("Decisions", a.decisions),
    ]

    # Defensive stats
    def_stats = [
        stat_bar("Tackling", a.tackling),
        stat_bar("Marking", a.marking),
    ]

    # GK stats (only for goalkeepers)
    gk_section = []
    if player.position.value == "GK":
        gk_section = [
            ft.Text("🧤 Goalkeeping", size=13, weight=ft.FontWeight.W_500,
                     color=theme.GOLD),
            stat_bar("Reflexes", a.gk_reflexes),
            stat_bar("Handling", a.gk_handling),
            stat_bar("GK Pos.", a.gk_positioning),
            stat_bar("1v1", a.gk_one_on_ones),
            stat_bar("Kicking", a.gk_kicking),
            ft.Divider(height=1),
        ]

    # Season stats row
    avg_rating_str = f"{s.average_rating:.1f}" if s.average_rating > 0 else "—"

    # ── Chart data ──────────────────────────────────────────────────
    from src.data.chart_queries import get_player_match_ratings
    from src.ui.widgets.charts import player_form_line_chart, player_stats_bar_chart
    from src.ui.app import app_state as _app_state

    match_ratings = []
    if _app_state.db_conn:
        try:
            match_ratings = get_player_match_ratings(_app_state.db_conn, player.id, limit=10)
        except Exception:
            pass

    form_chart = player_form_line_chart(match_ratings, width=270, height=130)

    # Attribute category averages
    tech_avg = (a.finishing + a.passing + a.dribbling + a.first_touch +
                a.crossing + a.heading + a.long_shots) / 7
    phys_avg = (a.pace + a.stamina + a.strength + a.agility + a.jumping) / 5
    mental_avg = (a.composure + a.vision + a.work_rate + a.positioning + a.decisions) / 5
    def_avg = (a.tackling + a.marking) / 2
    attr_categories = {
        "Tech": round(tech_avg, 1),
        "Phys": round(phys_avg, 1),
        "Mental": round(mental_avg, 1),
        "Def": round(def_avg, 1),
    }
    if player.position.value == "GK":
        gk_avg = (a.gk_reflexes + a.gk_handling + a.gk_positioning +
                  a.gk_one_on_ones + a.gk_kicking) / 5
        attr_categories["GK"] = round(gk_avg, 1)

    attr_chart = player_stats_bar_chart(attr_categories, width=270, height=120)

    season_info = ft.Row(
        wrap=True, spacing=12,
        controls=[
            ft.Text(f"⚽ {s.goals}G", size=12),
            ft.Text(f"🅰️ {s.assists}A", size=12),
            ft.Text(f"📋 {s.appearances} Apps", size=12),
            ft.Text(f"⭐ {avg_rating_str}", size=12),
            ft.Text(f"🟡 {s.yellow_cards}", size=12),
            ft.Text(f"🟥 {s.red_cards}", size=12),
            ft.Text(f"🏅 {s.man_of_the_match} MOTM", size=12) if s.man_of_the_match > 0 else ft.Container(),
        ],
    )

    # Contract info
    expiry_str = player.contract.contract_expiry.strftime("%b %Y") if player.contract.contract_expiry else "N/A"
    wage_str = f"{player.contract.wage_weekly:,} EGP/wk"

    # Secondary positions
    sec_pos_text = ", ".join(p.value for p in player.secondary_positions) if player.secondary_positions else "None"

    # Performance ratios
    mins_per_goal = "—"
    if s.goals > 0 and s.minutes_played > 0:
        mins_per_goal = str(s.minutes_played // s.goals)
    mins_per_assist = "—"
    if s.assists > 0 and s.minutes_played > 0:
        mins_per_assist = str(s.minutes_played // s.assists)

    # Form trend arrow
    if s.average_rating > 0 and player.form > 0:
        if player.form > s.average_rating + 0.3:
            form_trend = "📈 Rising"
            form_trend_color = ft.Colors.GREEN_400
        elif player.form < s.average_rating - 0.3:
            form_trend = "📉 Declining"
            form_trend_color = ft.Colors.RED_400
        else:
            form_trend = "➡️ Steady"
            form_trend_color = ft.Colors.GREY_400
    else:
        form_trend = "—"
        form_trend_color = ft.Colors.GREY_500

    # Training focus dropdown
    from src.core.training import get_training_programs, get_recommended_focus
    training_programs = get_training_programs()
    recommended = get_recommended_focus(player)
    training_options = [ft.dropdown.Option("", text="None")] + [
        ft.dropdown.Option(k, text=f"{'⭐ ' if k == recommended else ''}{k}")
        for k in training_programs
    ]

    def on_training_change(e):
        from src.ui.app import app_state, show_snackbar
        new_focus = e.control.value or ""
        player.training_focus = new_focus
        queries.update_player_stats(app_state.db_conn, player)
        label = new_focus if new_focus else "None"
        show_snackbar(page, f"Training focus set to {label} for {player.name}")

    training_dd = ft.Dropdown(
        label="Training Focus",
        value=player.training_focus or "",
        options=training_options,
        on_select=on_training_change,
        width=200, text_size=12,
    )

    # Development plan dropdown (long-term arcs / position retraining)
    from src.core.development import PLANS

    def on_dev_change(e):
        from src.ui.app import app_state, show_snackbar
        v = e.control.value or "none"
        player.dev_plan = "" if v == "none" else v
        if not player.dev_plan:
            player.dev_progress = 0
        _pct = min(100, int(getattr(player, "dev_progress", 0)))
        dev_progress_bar.value = _pct / 100.0
        dev_progress_text.value = (
            f"{_pct}% complete" if player.dev_plan else "No active plan."
        )
        queries.update_player_stats(app_state.db_conn, player)
        label = PLANS.get(v, {}).get("label", "No plan")
        show_snackbar(page, f"{player.name}: {label}")

    dev_dd = ft.Dropdown(
        label="Development Plan",
        value=getattr(player, "dev_plan", "") or "none",
        options=[ft.dropdown.Option("none", text="None")] + [
            ft.dropdown.Option(k, text=v["label"]) for k, v in PLANS.items()
        ],
        on_select=on_dev_change,
        width=200, text_size=12,
    )

    _dp = min(100, int(getattr(player, "dev_progress", 0)))
    dev_progress_bar = ft.ProgressBar(value=_dp / 100.0, width=200)
    dev_progress_text = ft.Text(
        f"{_dp}% complete" if getattr(player, "dev_plan", "") else "No active plan.",
        size=10, color=ft.Colors.GREY_500,
    )

    dlg = ft.AlertDialog(
        title=ft.Row(
            controls=[
                ft.Text(player.name, size=18, weight=ft.FontWeight.BOLD,
                        color=theme.GOLD, expand=True),
                ft.Container(
                    content=ft.Text(str(ovr), size=18, weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.GREEN_300 if ovr >= 70 else ft.Colors.WHITE),
                    bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.GREEN),
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=10,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.GREEN)),
                ),
            ],
        ),
        content=ft.Container(
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                spacing=6,
                controls=[
                    # Player info bar
                    ft.Row(
                        spacing=10, wrap=True,
                        controls=[
                            ft.Text(f"📍 {player.position.value}", size=12,
                                    color=theme.GOLD, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Age {player.age}", size=12),
                            ft.Text(f"🦶 {player.preferred_foot.value}", size=12),
                            ft.Text(f"#{player.shirt_number or '–'}", size=12,
                                    color=ft.Colors.GREY_400),
                        ],
                    ),
                    ft.Row(
                        spacing=10, wrap=True,
                        controls=[
                            ft.Text(f"🌍 {player.nationality}", size=11, color=ft.Colors.GREY_400),
                            ft.Text(f"🏠 {player.governorate}", size=11, color=ft.Colors.GREY_400),
                            ft.Text(f"🔄 Alt: {sec_pos_text}", size=11, color=ft.Colors.GREY_400),
                        ],
                    ),
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Text(f"💪 {player.fitness}%", size=12, color=fit_color),
                            ft.Text(f"📊 Form {player.form:.1f}", size=12),
                            ft.Text(f"😊 {morale_desc}", size=11, color=morale_color,
                                     max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(form_trend, size=11, color=form_trend_color),
                        ],
                    ),
                    *(status_badges if status_badges else []),
                    ft.Divider(height=1),
                    # Season stats
                    ft.Text("📈 Season Stats", size=13, weight=ft.FontWeight.W_500,
                             color=theme.GOLD),
                    season_info,
                    ft.Row(
                        spacing=12, wrap=True,
                        controls=[
                            ft.Text(f"⏱️ {s.minutes_played} mins", size=11, color=ft.Colors.GREY_400),
                            ft.Text(f"Mins/Goal: {mins_per_goal}", size=11, color=ft.Colors.GREY_400),
                            ft.Text(f"Mins/Assist: {mins_per_assist}", size=11, color=ft.Colors.GREY_400),
                        ],
                    ),
                    ft.Divider(height=1),
                    # Form chart
                    ft.Text("📊 Form Trend", size=13, weight=ft.FontWeight.W_500,
                             color=theme.GOLD),
                    form_chart,
                    ft.Divider(height=1),
                    # Attribute overview chart
                    ft.Text("📈 Attribute Overview", size=13, weight=ft.FontWeight.W_500,
                             color=theme.GOLD),
                    attr_chart,
                    ft.Divider(height=1),
                    # GK section (if applicable)
                    *gk_section,
                    # Technical
                    ft.Text("⚽ Technical", size=13, weight=ft.FontWeight.W_500,
                             color=theme.GOLD),
                    *tech_stats,
                    ft.Divider(height=1),
                    # Defensive
                    ft.Text("🛡️ Defensive", size=13, weight=ft.FontWeight.W_500,
                             color=theme.GOLD),
                    *def_stats,
                    ft.Divider(height=1),
                    # Physical
                    ft.Text("🏃 Physical", size=13, weight=ft.FontWeight.W_500,
                             color=theme.GOLD),
                    *phys_stats,
                    ft.Divider(height=1),
                    # Mental
                    ft.Text("🧠 Mental", size=13, weight=ft.FontWeight.W_500,
                             color=theme.GOLD),
                    *mental_stats,
                    ft.Divider(height=1),
                    # Contract
                    ft.Text("📝 Contract", size=13, weight=ft.FontWeight.W_500,
                             color=theme.GOLD),
                    ft.Row(
                        spacing=15,
                        controls=[
                            ft.Text(f"💰 {wage_str}", size=12),
                            ft.Text(f"📅 Expires: {expiry_str}", size=12),
                        ],
                    ),
                    ft.Divider(height=1),
                    # Training
                    ft.Text("🏋️ Training", size=13, weight=ft.FontWeight.W_500,
                             color=theme.GOLD),
                    training_dd,
                    ft.Text("🎯 Development Plan", size=13, weight=ft.FontWeight.W_500,
                             color=theme.GOLD),
                    ft.Text(
                        "Season-long arc: weekly attribute growth toward a target "
                        "role. Retrain plans can change a player's position.",
                        size=10, color=ft.Colors.GREY_500,
                    ),
                    dev_dd,
                    dev_progress_bar,
                    dev_progress_text,
                ],
            ),
            width=290,
            height=420,
        ),
        actions=[
            ft.TextButton(
                "© Captain" if not player.is_captain else "✓ Captain",
                on_click=lambda e, pid=player.id: _set_captain(page, pid),
                style=ft.ButtonStyle(color=theme.GOLD),
            ),
            ft.TextButton(
                "🗣️ Talk",
                on_click=lambda e, pid=player.id, pname=player.name: _talk_to_player(page, pid, pname),
            ),
            ft.TextButton(
                "📤 List" if not player.transfer_listed else "🔴 Unlist",
                on_click=lambda e, pid=player.id, listed=player.transfer_listed: _toggle_transfer(page, pid, listed),
                style=ft.ButtonStyle(color=ft.Colors.RED_400) if player.transfer_listed else None,
            ),
            ft.TextButton(
                "📝 Renew",
                on_click=lambda e, pid=player.id: _renew_contract(page, pid),
            ),
            ft.TextButton("Close", on_click=lambda e: page.pop_dialog()),
        ],
    )
    page.show_dialog(dlg)


def _set_captain(page, player_id):
    """Set a player as captain."""
    from src.ui.app import app_state, navigate, show_snackbar
    conn = app_state.db_conn
    gs = app_state.game_state
    queries.set_captain(conn, gs.user_club_id, player_id)
    page.pop_dialog()
    show_snackbar(page, "Captain updated!")
    navigate(page, "/squad")


def _toggle_transfer(page, player_id, currently_listed):
    """Toggle transfer list status."""
    from src.ui.app import app_state, navigate, show_snackbar
    conn = app_state.db_conn
    queries.set_transfer_listed(conn, player_id, not currently_listed)
    page.pop_dialog()
    msg = "Player removed from transfer list." if currently_listed else "Player listed for transfer!"
    show_snackbar(page, msg)
    navigate(page, "/squad")


def _talk_to_player(page, player_id, player_name):
    """Show a player interaction dialog — praise, encourage, criticize, or discuss playing time."""
    from src.ui.app import app_state, navigate, show_snackbar
    from src.core.player import get_morale_description
    from src.data.models import InboxMessage
    from src.utils import rng

    conn = app_state.db_conn
    gs = app_state.game_state
    player = queries.get_player(conn, player_id)
    if not player:
        return

    morale_desc = get_morale_description(player)
    result_text = ft.Text("", size=12)

    talks = [
        ("💪 Praise Performance", "praise",
         "Great work out there! Keep it up.",
         "The player appreciates the recognition."),
        ("🔥 Demand More Effort", "criticize",
         "I expect much more from you!",
         "The player reacts to the criticism."),
        ("🤝 Encourage", "encourage",
         "I believe in you. Show me what you can do.",
         "The player feels encouraged."),
        ("⏱️ Promise Playing Time", "promise_time",
         "Your chance will come, be patient.",
         "The player acknowledges the promise."),
    ]

    def make_handler(talk_type, response_text):
        def handler(e):
            morale_change = 0
            feedback = ""

            if talk_type == "praise":
                if player.form >= 7.0:
                    morale_change = rng.randint(3, 8)
                    feedback = f"😊 {player_name} is delighted by the praise! Morale +{morale_change}"
                else:
                    morale_change = rng.randint(0, 3)
                    feedback = f"😐 {player_name} appreciates the words but knows they can do better."

            elif talk_type == "criticize":
                if player.morale >= 60 and player.attributes.composure >= 12:
                    morale_change = rng.randint(-2, 2)
                    feedback = f"💪 {player_name} takes the criticism on board and is determined to improve."
                elif player.morale < 40:
                    morale_change = rng.randint(-8, -3)
                    feedback = f"😤 {player_name} doesn't take it well. The player storms out of the office!"
                else:
                    morale_change = rng.randint(-5, 0)
                    feedback = f"😕 {player_name} is unhappy with the criticism but will try harder."

            elif talk_type == "encourage":
                morale_change = rng.randint(2, 6)
                feedback = f"😊 {player_name} feels motivated by your words! Morale +{morale_change}"
                if player.age <= 21:
                    morale_change += 2
                    feedback += "\n📈 The young player especially benefits from the encouragement."

            elif talk_type == "promise_time":
                if player.matches_benched_streak >= 3:
                    morale_change = rng.randint(3, 7)
                    feedback = f"😊 {player_name} is relieved to hear they'll get a chance. Morale +{morale_change}"
                else:
                    morale_change = rng.randint(-1, 2)
                    feedback = f"😐 {player_name}: \"I'm already getting games, boss.\""

            # Apply morale change
            from src.utils.rng import clamp
            player.morale = int(clamp(player.morale + morale_change, 0, 100))
            queries.update_player_stats(conn, player)

            # Send inbox message
            queries.insert_message(conn, InboxMessage(
                date=gs.current_date,
                subject=f"🗣️ Talk: {player_name}",
                body=feedback,
                category="general",
            ))

            result_text.value = feedback
            result_text.color = (ft.Colors.GREEN_400 if morale_change > 0
                                  else ft.Colors.RED_400 if morale_change < 0
                                  else ft.Colors.GREY_400)
            page.update()
        return handler

    talk_buttons = []
    for label, talk_type, msg, resp in talks:
        talk_buttons.append(
            ft.Container(
                content=ft.Column(spacing=1, controls=[
                    ft.Text(label, size=13, weight=ft.FontWeight.W_500),
                    ft.Text(msg, size=10, color=ft.Colors.GREY_500, italic=True),
                ]),
                padding=ft.padding.symmetric(horizontal=10, vertical=10),
                border_radius=10,
                bgcolor=theme.CARD_GLASS,
                border=ft.border.all(1, theme.GOLD_BORDER),
                on_click=make_handler(talk_type, resp),
                ink=True,
            )
        )

    dlg = ft.AlertDialog(
        title=ft.Text(f"🗣️ Talk to {player_name}", size=15,
                       weight=ft.FontWeight.BOLD, color=theme.GOLD),
        content=ft.Container(
            content=ft.Column(spacing=6, controls=[
                ft.Text(f"Current mood: {morale_desc}", size=12, color=ft.Colors.GREY_400),
                ft.Text(f"Morale: {player.morale}/100", size=12),
                ft.Divider(height=1),
                *talk_buttons,
                ft.Divider(height=1),
                result_text,
            ]),
            width=290, height=320,
        ),
        actions=[
            ft.TextButton("Done", on_click=lambda e: (page.pop_dialog(), navigate(page, "/squad"))),
        ],
    )
    page.show_dialog(dlg)


def _renew_contract(page, player_id):
    """Show a contract renewal negotiation dialog."""
    from src.ui.app import app_state, navigate, show_snackbar
    conn = app_state.db_conn
    player = queries.get_player(conn, player_id)
    if not player:
        return

    current_wage = player.contract.wage_weekly
    # Player expects at least 10% raise; bigger stars want more
    from src.core.player import calculate_overall_rating
    ovr = calculate_overall_rating(player)
    min_raise_pct = 5 if ovr < 60 else 10 if ovr < 70 else 15 if ovr < 80 else 20
    min_acceptable = int(current_wage * (1 + min_raise_pct / 100))

    expiry_str = player.contract.contract_expiry.strftime("%b %Y") if player.contract.contract_expiry else "N/A"

    years_dd = ft.Dropdown(
        label="Contract Length",
        value="2",
        options=[ft.dropdown.Option("1", text="1 year"),
                 ft.dropdown.Option("2", text="2 years"),
                 ft.dropdown.Option("3", text="3 years"),
                 ft.dropdown.Option("4", text="4 years")],
        width=180,
    )

    wage_field = ft.TextField(
        label="Weekly Wage Offer (EGP)",
        value=str(min_acceptable),
        width=180, text_size=13,
    )

    result_text = ft.Text("", size=12, color=ft.Colors.GREY_400)

    def submit_renewal(e):
        try:
            offered_wage = int(wage_field.value)
            years = int(years_dd.value)
        except ValueError:
            show_snackbar(page, "Enter valid numbers!", bgcolor=ft.Colors.RED_800)
            return

        if offered_wage < min_acceptable:
            result_text.value = (
                f"❌ {player.name} wants at least {min_acceptable:,} EGP/wk. "
                f"Your offer of {offered_wage:,} is too low."
            )
            result_text.color = ft.Colors.RED_400
            page.update()
            return

        # Check wage budget
        club = queries.get_club(conn, app_state.game_state.user_club_id)
        if club:
            wage_increase = offered_wage - current_wage
            if club.finances.wage_bill_weekly + wage_increase > club.finances.wage_budget_weekly:
                result_text.value = "❌ Cannot afford this wage increase!"
                result_text.color = ft.Colors.RED_400
                page.update()
                return

        # Use AI-driven contract renewal acceptance logic
        from src.core.transfers import offer_contract_renewal
        gs = app_state.game_state
        accepted, msg = offer_contract_renewal(conn, gs, player_id, offered_wage, years)

        if accepted:
            page.pop_dialog()
            show_snackbar(page, f"✅ {msg}")
            try:
                page.pop_dialog()
            except Exception:
                pass
            navigate(page, "/squad")
        else:
            result_text.value = f"❌ {msg}"
            result_text.color = ft.Colors.RED_400
            page.update()

    renewal_dlg = ft.AlertDialog(
        title=ft.Text(f"📝 Renew: {player.name}", size=16,
                       weight=ft.FontWeight.BOLD, color=theme.GOLD),
        content=ft.Container(
            content=ft.Column(spacing=8, controls=[
                ft.Row(spacing=10, controls=[
                    ft.Text(f"Current wage: {current_wage:,} EGP/wk", size=12),
                    ft.Text(f"Expires: {expiry_str}", size=12, color=ft.Colors.GREY_400),
                ]),
                ft.Text(f"Player expects: ≥{min_acceptable:,} EGP/wk (+{min_raise_pct}%)",
                        size=11, color=theme.GOLD, italic=True),
                years_dd,
                wage_field,
                result_text,
            ]),
            width=300, height=220,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
            ft.ElevatedButton("Offer", on_click=submit_renewal,
                              style=ft.ButtonStyle(bgcolor=theme.ACCENT_DARK,
                                                   color=ft.Colors.WHITE)),
        ],
    )
    page.show_dialog(renewal_dlg)


def _save_game(page, conn, gs):
    """Save the current game state."""
    from src.ui.app import show_snackbar
    queries.save_game_state(conn, gs)
    show_snackbar(page, "💾 Game saved!")


def _start_compare(page, players):
    """Let the user pick two players to compare."""
    from src.ui.app import show_snackbar

    selected = [None, None]

    def make_pick_handler(p, idx):
        def handler(e):
            selected[idx] = p
            if selected[0] and selected[1]:
                page.pop_dialog()
                _show_compare_dialog(page, selected[0], selected[1])
        return handler

    player_list_1 = []
    for p in players:
        ovr = calculate_overall_rating(p)
        player_list_1.append(
            ft.ListTile(
                title=ft.Text(f"{p.name} ({p.position.value})", size=12),
                subtitle=ft.Text(f"OVR {ovr} | Age {p.age}", size=10, color=ft.Colors.GREY_400),
                on_click=make_pick_handler(p, 0),
            )
        )

    step_text = ft.Text("Pick Player 1", size=14, weight=ft.FontWeight.BOLD,
                         color=theme.GOLD)

    def rebuild_for_p2():
        """After picking player 1, rebuild list for player 2."""
        step_text.value = f"✅ {selected[0].name} — Now pick Player 2"
        list_view.controls.clear()
        for p in players:
            if p.id == selected[0].id:
                continue
            ovr = calculate_overall_rating(p)
            list_view.controls.append(
                ft.ListTile(
                    title=ft.Text(f"{p.name} ({p.position.value})", size=12),
                    subtitle=ft.Text(f"OVR {ovr} | Age {p.age}", size=10, color=ft.Colors.GREY_400),
                    on_click=make_pick_handler(p, 1),
                )
            )
        page.update()

    # Override pick handler for step 1
    def make_step1_handler(p):
        def handler(e):
            selected[0] = p
            rebuild_for_p2()
        return handler

    list_view = ft.ListView(spacing=2, height=340, controls=[])
    for p in players:
        ovr = calculate_overall_rating(p)
        list_view.controls.append(
            ft.ListTile(
                title=ft.Text(f"{p.name} ({p.position.value})", size=12),
                subtitle=ft.Text(f"OVR {ovr} | Age {p.age}", size=10, color=ft.Colors.GREY_400),
                on_click=make_step1_handler(p),
            )
        )

    dlg = ft.AlertDialog(
        title=ft.Text("⚖️ Compare Players", color=theme.GOLD),
        content=ft.Container(
            content=ft.Column(controls=[step_text, list_view], spacing=6, tight=True),
            width=290, height=400,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        ),
        actions=[ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog())],
    )
    page.show_dialog(dlg)


def _show_compare_dialog(page, p1, p2):
    """Show side-by-side player comparison."""
    ovr1 = calculate_overall_rating(p1)
    ovr2 = calculate_overall_rating(p2)

    attrs_to_compare = [
        (t("finishing"), "finishing"), (t("passing"), "passing"), (t("dribbling"), "dribbling"),
        (t("first_touch"), "first_touch"), (t("crossing"), "crossing"), (t("heading"), "heading"),
        (t("pace"), "pace"), (t("stamina"), "stamina"), (t("strength"), "strength"),
        (t("agility"), "agility"), (t("composure"), "composure"), (t("vision"), "vision"),
        (t("tackling"), "tackling"), (t("marking"), "marking"), (t("work_rate"), "work_rate"),
        (t("positioning"), "positioning")
    ]

    rows = []
    for label, attr in attrs_to_compare:
        v1 = getattr(p1.attributes, attr, 10)
        v2 = getattr(p2.attributes, attr, 10)
        c1 = ft.Colors.GREEN_400 if v1 > v2 else (ft.Colors.RED_400 if v1 < v2 else ft.Colors.WHITE)
        c2 = ft.Colors.GREEN_400 if v2 > v1 else (ft.Colors.RED_400 if v2 < v1 else ft.Colors.WHITE)
        rows.append(ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(str(v1), size=12, weight=ft.FontWeight.BOLD, color=c1, width=30),
                ft.Text(label, size=10, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER, expand=True),
                ft.Text(str(v2), size=12, weight=ft.FontWeight.BOLD, color=c2, width=30,
                         text_align=ft.TextAlign.RIGHT),
            ],
        ))

    dlg = ft.AlertDialog(
        title=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text(p1.name, size=13, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{p1.position.value} | OVR {ovr1}", size=10, color=theme.GOLD),
                ]),
                ft.Text("VS", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_500),
                ft.Column(spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text(p2.name, size=13, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{p2.position.value} | OVR {ovr2}", size=10, color=theme.GOLD),
                ]),
            ],
        ),
        content=ft.Container(
            content=ft.Column(controls=rows, spacing=4, scroll=ft.ScrollMode.AUTO),
            width=290, height=380,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        ),
        actions=[ft.TextButton("Close", on_click=lambda e: page.pop_dialog())],
    )
    page.show_dialog(dlg)


def _build_career_bar(conn, page) -> list:
    """Build the career stats strip + achievements button."""
    from src.core.achievements import load_career, get_achievements, seed_achievements
    try:
        seed_achievements(conn)  # Ensure tables exist
        career = load_career(conn)
    except Exception:
        return []

    total = career["total_wins"] + career["total_draws"] + career["total_losses"]
    if total == 0:
        return []  # No matches played yet

    win_pct = career["total_wins"] / total * 100

    # Count unlocked achievements
    achs = get_achievements(conn)
    unlocked_count = sum(1 for a in achs if a["unlocked"])
    total_achs = len(achs)

    rating_color = (
        ft.Colors.GREEN_400 if career["manager_rating"] >= 65
        else theme.GOLD if career["manager_rating"] >= 45
        else ft.Colors.RED_400
    )

    def show_achievements(e):
        _show_achievements_dialog(page, conn)

    career_row = ft.Container(
        content=ft.Column(spacing=4, controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("📊 Manager Career", size=12, weight=ft.FontWeight.W_500,
                            color=theme.GOLD),
                    ft.Container(
                        content=ft.Text(f"⭐ {career['manager_rating']:.0f}",
                                        size=12, weight=ft.FontWeight.BOLD,
                                        color=rating_color),
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        border_radius=6,
                        bgcolor=ft.Colors.with_opacity(0.1, rating_color),
                    ),
                ],
            ),
            ft.Row(
                spacing=0,
                controls=[
                    ft.Text(f"W{career['total_wins']}", size=11,
                            color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD, width=40),
                    ft.Text(f"D{career['total_draws']}", size=11,
                            color=ft.Colors.YELLOW_400, width=30),
                    ft.Text(f"L{career['total_losses']}", size=11,
                            color=ft.Colors.RED_400, width=30),
                    ft.Text(f"{win_pct:.0f}%", size=11, color=ft.Colors.GREY_400, width=35),
                    ft.Container(expand=True),
                    ft.Text(f"🔥{career['longest_win_streak']}", size=10,
                            color=ft.Colors.GREY_500, width=30),
                    ft.Text(f"🧤{career['clean_sheets']}", size=10,
                            color=ft.Colors.GREY_500, width=30),
                    ft.Text(f"⚽{career['total_goals_scored']}", size=10,
                            color=ft.Colors.GREY_500, width=35),
                ],
            ),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(f"🏆 {unlocked_count}/{total_achs} achievements", size=10,
                            color=ft.Colors.GREY_500),
                    ft.TextButton("View All →", on_click=show_achievements,
                                   style=ft.ButtonStyle(
                                       text_style=ft.TextStyle(size=10))),
                ],
            ),
        ]),
        padding=ft.padding.symmetric(horizontal=10, vertical=8),
        border_radius=10,
        bgcolor=theme.CARD_GLASS,
        border=ft.border.all(1, theme.GOLD_BORDER),
    )
    return [career_row]


def _show_achievements_dialog(page, conn):
    """Show all achievements in a dialog."""
    from src.core.achievements import get_achievements
    achs = get_achievements(conn)

    rows = []
    for a in achs:
        if a["unlocked"]:
            rows.append(ft.Container(
                content=ft.Row(spacing=8, controls=[
                    ft.Text(a["icon"], size=22),
                    ft.Column(spacing=0, expand=True, controls=[
                        ft.Text(a["title"], size=12, weight=ft.FontWeight.BOLD,
                                color=theme.GOLD),
                        ft.Text(a["description"], size=10, color=ft.Colors.GREY_400),
                    ]),
                    ft.Text(a["unlock_date"][:10] if a["unlock_date"] else "",
                            size=9, color=ft.Colors.GREY_600),
                ]),
                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.AMBER),
                border=ft.border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.AMBER)),
            ))
        else:
            rows.append(ft.Container(
                content=ft.Row(spacing=8, controls=[
                    ft.Text("🔒", size=18, color=ft.Colors.GREY_700),
                    ft.Column(spacing=0, expand=True, controls=[
                        ft.Text(a["title"], size=12, color=ft.Colors.GREY_600),
                        ft.Text(a["description"], size=10, color=ft.Colors.GREY_700),
                    ]),
                ]),
                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                border=ft.border.all(1, ft.Colors.with_opacity(0.06, ft.Colors.WHITE)),
            ))

    dlg = ft.AlertDialog(
        title=ft.Text("🏆 Achievements", size=16,
                       weight=ft.FontWeight.BOLD, color=theme.GOLD),
        content=ft.Container(
            content=ft.Column(spacing=4, controls=rows, scroll=ft.ScrollMode.AUTO),
            width=300, height=400,
        ),
        actions=[ft.TextButton("Close", on_click=lambda e: page.pop_dialog())],
    )
    page.show_dialog(dlg)
