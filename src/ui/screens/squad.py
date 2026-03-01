"""
Squad management screen — view players, tap for detailed stats.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.core.player import calculate_overall_rating
from src.ui.widgets.nav_bar import build_nav_bar
from src.ui.widgets.stat_bar import stat_bar


def build_squad_screen(page: ft.Page) -> ft.Column:
    """Build the squad management content."""
    from src.ui.app import app_state, navigate

    page.navigation_bar = build_nav_bar(page, 0)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text("No game loaded")])

    conn = app_state.db_conn
    gs = app_state.game_state
    club = queries.get_club(conn, gs.user_club_id)
    if not club:
        return ft.Column(controls=[ft.Text("Club not found")])

    players = queries.get_players_by_club(conn, club.id)

    # Sorting
    sort_options = {
        "Position": lambda p: (p.position.value, -calculate_overall_rating(p)),
        "OVR ↓": lambda p: -calculate_overall_rating(p),
        "Age": lambda p: p.age,
        "Fitness": lambda p: -p.fitness,
        "Form ↓": lambda p: -p.form,
        "Morale": lambda p: -p.morale,
    }
    default_sort = "Position"
    players.sort(key=sort_options[default_sort])

    # Build player rows for the DataTable
    def _build_rows(sorted_players):
        rows = []
        for player in sorted_players:
            ovr = calculate_overall_rating(player)
            fit_color = (
                ft.Colors.GREEN_400 if player.fitness >= 80
                else ft.Colors.YELLOW_400 if player.fitness >= 50
                else ft.Colors.RED_400
            )
            ovr_color = ft.Colors.GREEN_300 if ovr >= 70 else ft.Colors.WHITE

            # Name with badges
            name_parts = [player.name]
            if player.is_captain:
                name_parts.append("©")
            if player.transfer_listed:
                name_parts.append("🔴")
            if player.injury_days_remaining > 0:
                name_parts.append("🏥")
            if player.suspension_matches > 0:
                name_parts.append("🚫")
            display_name = " ".join(name_parts)

            def make_click_handler(p=player, o=ovr):
                def handler(e):
                    _show_player_detail(page, p, o)
                return handler

            # Training focus emoji
            train_map = {
                "Shooting": "⚽", "Defending": "🛡️", "Physical": "🏃",
                "Playmaking": "🎯", "Mental": "🧠",
            }
            train_label = train_map.get(player.training_focus, "—")

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(display_name, size=12)),
                        ft.DataCell(ft.Text(player.position.value, size=11,
                                            color=ft.Colors.AMBER_300)),
                        ft.DataCell(ft.Text(str(player.age), size=11)),
                        ft.DataCell(ft.Text(str(ovr), size=12,
                                            weight=ft.FontWeight.BOLD, color=ovr_color)),
                        ft.DataCell(ft.Text(f"{player.fitness}%", size=11, color=fit_color)),
                        ft.DataCell(ft.Text(f"{player.form:.1f}", size=11)),
                        ft.DataCell(ft.Text(
                            "😊" if player.morale >= 70 else "😐" if player.morale >= 40 else "😞",
                            size=13,
                        )),
                        ft.DataCell(ft.Text(train_label, size=12)),
                    ],
                    on_select_change=make_click_handler(),
                )
            )
        return rows

    rows = _build_rows(players)

    # Squad summary
    avg_ovr = sum(calculate_overall_rating(p) for p in players) / max(len(players), 1)
    avg_age = sum(p.age for p in players) / max(len(players), 1)

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text("Name", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(label=ft.Text("Pos", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(label=ft.Text("Age", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(label=ft.Text("OVR", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(label=ft.Text("Fit", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(label=ft.Text("Form", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(label=ft.Text("😊", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(label=ft.Text("🏋️", size=11, weight=ft.FontWeight.BOLD)),
        ],
        rows=rows,
        column_spacing=10,
        horizontal_lines=ft.BorderSide(0.3, ft.Colors.WHITE24),
        heading_row_height=35,
        data_row_min_height=34,
        data_row_max_height=38,
    )

    def on_sort_change(e):
        key = e.control.value
        sort_fn = sort_options.get(key, sort_options["Position"])
        players.sort(key=sort_fn)
        data_table.rows = _build_rows(players)
        page.update()

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=ft.padding.only(left=10, right=10, top=10),
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    f"📋 {gs.user_club_name}",
                                    size=22, weight=ft.FontWeight.BOLD,
                                ),
                                ft.Row(spacing=4, controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.COMPARE_ARROWS, tooltip="Compare Players",
                                        icon_size=20,
                                        on_click=lambda e: _start_compare(page, players),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.SAVE, tooltip="Save Game",
                                        icon_size=20,
                                        on_click=lambda e: _save_game(page, conn, gs),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.STORE, tooltip="Transfer Market",
                                        icon_size=20,
                                        on_click=lambda e: navigate(page, "/transfers"),
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.SETTINGS, tooltip="Settings",
                                        icon_size=20,
                                        on_click=lambda e: navigate(page, "/settings"),
                                    ),
                                ]),
                            ],
                        ),
                        ft.Row(
                            spacing=15,
                            controls=[
                                ft.Text(
                                    f"👤 {gs.manager_name}",
                                    size=13, color=ft.Colors.GREY_400,
                                ),
                                ft.Text(
                                    f"📅 {gs.current_date.strftime('%d %b %Y')}",
                                    size=13, color=ft.Colors.GREY_500,
                                ),
                                ft.TextButton(
                                    "🏟️ Club",
                                    on_click=lambda e: navigate(page, "/club"),
                                    style=ft.ButtonStyle(padding=0),
                                ),
                            ],
                        ),
                        # Squad summary chips
                        ft.Row(
                            spacing=8,
                            controls=[
                                _summary_chip("Squad", str(len(players)), ft.Icons.PEOPLE),
                                _summary_chip("Avg OVR", f"{avg_ovr:.0f}", ft.Icons.STAR),
                                _summary_chip("Avg Age", f"{avg_age:.1f}", ft.Icons.CAKE),
                            ],
                        ),
                        # News ticker
                        _build_news_ticker(conn, gs),
                        ft.Divider(height=1),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("Tap a player for details",
                                        size=11, color=ft.Colors.GREY_600, italic=True),
                                ft.Dropdown(
                                    label="Sort",
                                    value=default_sort,
                                    options=[ft.dropdown.Option(k) for k in sort_options],
                                    on_select=on_sort_change,
                                    width=120,
                                    text_size=11,
                                ),
                            ],
                        ),
                        data_table,
                    ],
                ),
            ),
        ],
    )


def _build_news_ticker(conn, gs) -> ft.Container:
    """Build a compact league news ticker showing position, upcoming match, and recent results."""
    items = []

    # League position
    try:
        standings = queries.get_standings(conn)
        for i, s in enumerate(standings, 1):
            if s.club_id == gs.user_club_id:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(i if i < 20 else i % 10, "th")
                items.append(
                    ft.Text(f"🏆 {i}{suffix} — {s.points}pts (W{s.won} D{s.drawn} L{s.lost})",
                             size=11, color=ft.Colors.GREY_400)
                )
                break
    except Exception:
        pass

    # Upcoming fixture
    next_fix = queries.get_user_next_fixture(conn, gs.user_club_id)
    if next_fix:
        is_home = next_fix.home_club_id == gs.user_club_id
        opp = next_fix.away_club_name if is_home else next_fix.home_club_name
        venue = "H" if is_home else "A"
        if next_fix.date:
            days = (next_fix.date - gs.current_date).days
            when = "TODAY" if days <= 0 else f"in {days}d"
        else:
            when = "TBD"
        items.append(
            ft.Text(f"📅 Next: vs {opp} ({venue}) {when}", size=11,
                     color=ft.Colors.AMBER_300, weight=ft.FontWeight.W_500)
        )

    # Last matchday results (up to 4)
    played_mds = queries.get_all_matchdays_played(conn)
    if played_mds:
        last_md = played_mds[0]
        results = queries.get_matchday_results(conn, last_md)
        for fix in results[:4]:
            r = fix.result
            if not r:
                continue
            is_user = (fix.home_club_id == gs.user_club_id or fix.away_club_id == gs.user_club_id)
            color = ft.Colors.GREEN_300 if is_user else ft.Colors.GREY_500
            items.append(
                ft.Text(f"  {fix.home_club_name[:10]} {r.home_goals}-{r.away_goals} {fix.away_club_name[:10]}",
                         size=10, color=color)
            )

    if not items:
        return ft.Container()

    return ft.Container(
        content=ft.Column(controls=items, spacing=2),
        padding=ft.padding.symmetric(horizontal=4, vertical=4),
        border_radius=6,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
    )


def _summary_chip(label: str, value: str, icon) -> ft.Container:
    """Small summary chip widget."""
    return ft.Container(
        content=ft.Row(
            spacing=4, tight=True,
            controls=[
                ft.Icon(icon, size=13, color=ft.Colors.AMBER_300),
                ft.Text(f"{label}: ", size=10, color=ft.Colors.GREY_500),
                ft.Text(value, size=11, weight=ft.FontWeight.BOLD),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        border_radius=6,
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
    )


def _show_player_detail(page: ft.Page, player, ovr: int):
    """Show a detailed player profile dialog with all stats."""
    a = player.attributes
    s = player.season_stats

    fit_color = (
        ft.Colors.GREEN_400 if player.fitness >= 80
        else ft.Colors.YELLOW_400 if player.fitness >= 50
        else ft.Colors.RED_400
    )
    morale_text = (
        "😊 Happy" if player.morale >= 70
        else "😐 Content" if player.morale >= 40
        else "😞 Unhappy"
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
                     color=ft.Colors.AMBER_300),
            stat_bar("Reflexes", a.gk_reflexes),
            stat_bar("Handling", a.gk_handling),
            stat_bar("GK Pos.", a.gk_positioning),
            stat_bar("1v1", a.gk_one_on_ones),
            stat_bar("Kicking", a.gk_kicking),
            ft.Divider(height=1),
        ]

    # Season stats row
    avg_rating_str = f"{s.average_rating:.1f}" if s.average_rating > 0 else "—"
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

    dlg = ft.AlertDialog(
        title=ft.Row(
            controls=[
                ft.Text(player.name, size=18, weight=ft.FontWeight.BOLD, expand=True),
                ft.Container(
                    content=ft.Text(str(ovr), size=18, weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.GREEN_300 if ovr >= 70 else ft.Colors.WHITE),
                    bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.GREEN),
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=8,
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
                                    color=ft.Colors.AMBER_300, weight=ft.FontWeight.BOLD),
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
                            ft.Text(morale_text, size=12),
                            ft.Text(form_trend, size=11, color=form_trend_color),
                        ],
                    ),
                    *(status_badges if status_badges else []),
                    ft.Divider(height=1),
                    # Season stats
                    ft.Text("📈 Season Stats", size=13, weight=ft.FontWeight.W_500,
                             color=ft.Colors.AMBER_300),
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
                    # GK section (if applicable)
                    *gk_section,
                    # Technical
                    ft.Text("⚽ Technical", size=13, weight=ft.FontWeight.W_500,
                             color=ft.Colors.AMBER_300),
                    *tech_stats,
                    ft.Divider(height=1),
                    # Defensive
                    ft.Text("🛡️ Defensive", size=13, weight=ft.FontWeight.W_500,
                             color=ft.Colors.AMBER_300),
                    *def_stats,
                    ft.Divider(height=1),
                    # Physical
                    ft.Text("🏃 Physical", size=13, weight=ft.FontWeight.W_500,
                             color=ft.Colors.AMBER_300),
                    *phys_stats,
                    ft.Divider(height=1),
                    # Mental
                    ft.Text("🧠 Mental", size=13, weight=ft.FontWeight.W_500,
                             color=ft.Colors.AMBER_300),
                    *mental_stats,
                    ft.Divider(height=1),
                    # Contract
                    ft.Text("📝 Contract", size=13, weight=ft.FontWeight.W_500,
                             color=ft.Colors.AMBER_300),
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
                             color=ft.Colors.AMBER_300),
                    training_dd,
                ],
            ),
            width=340,
            height=420,
        ),
        actions=[
            ft.TextButton(
                "© Captain" if not player.is_captain else "✓ Captain",
                on_click=lambda e, pid=player.id: _set_captain(page, pid),
            ),
            ft.TextButton(
                "🔴 Unlist" if player.transfer_listed else "📤 List",
                on_click=lambda e, pid=player.id, listed=player.transfer_listed: _toggle_transfer(page, pid, listed),
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

        # Accept renewal
        from datetime import timedelta, date as dt_date
        base = player.contract.contract_expiry or dt_date.today()
        new_expiry = base + timedelta(days=365 * years)
        conn.execute(
            "UPDATE players SET contract_expiry = ?, wage_weekly = ? WHERE id = ?",
            (new_expiry.isoformat(), offered_wage, player_id)
        )
        conn.commit()

        page.pop_dialog()
        show_snackbar(page, f"📝 {player.name} renewed! {years}yr @ {offered_wage:,} EGP/wk")

        # Close the underlying player dialog too
        try:
            page.pop_dialog()
        except Exception:
            pass
        navigate(page, "/squad")

    renewal_dlg = ft.AlertDialog(
        title=ft.Text(f"📝 Renew: {player.name}", size=16, weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column(spacing=8, controls=[
                ft.Row(spacing=10, controls=[
                    ft.Text(f"Current wage: {current_wage:,} EGP/wk", size=12),
                    ft.Text(f"Expires: {expiry_str}", size=12, color=ft.Colors.GREY_400),
                ]),
                ft.Text(f"Player expects: ≥{min_acceptable:,} EGP/wk (+{min_raise_pct}%)",
                        size=11, color=ft.Colors.AMBER_300, italic=True),
                years_dd,
                wage_field,
                result_text,
            ]),
            width=300, height=220,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
            ft.ElevatedButton("Offer", on_click=submit_renewal,
                              style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_700,
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
                         color=ft.Colors.AMBER_300)

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

    list_view = ft.ListView(spacing=2, controls=[])
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
        title=ft.Text("⚖️ Compare Players"),
        content=ft.Container(
            content=ft.Column(controls=[step_text, list_view], spacing=6),
            width=330, height=400,
        ),
        actions=[ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog())],
    )
    page.show_dialog(dlg)


def _show_compare_dialog(page, p1, p2):
    """Show side-by-side player comparison."""
    ovr1 = calculate_overall_rating(p1)
    ovr2 = calculate_overall_rating(p2)

    attrs_to_compare = [
        ("Finishing", "finishing"), ("Passing", "passing"), ("Dribbling", "dribbling"),
        ("First Touch", "first_touch"), ("Crossing", "crossing"), ("Heading", "heading"),
        ("Pace", "pace"), ("Stamina", "stamina"), ("Strength", "strength"),
        ("Agility", "agility"), ("Composure", "composure"), ("Vision", "vision"),
        ("Tackling", "tackling"), ("Marking", "marking"), ("Work Rate", "work_rate"),
        ("Positioning", "positioning"),
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
                    ft.Text(f"{p1.position.value} | OVR {ovr1}", size=10, color=ft.Colors.AMBER_300),
                ]),
                ft.Text("VS", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_500),
                ft.Column(spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text(p2.name, size=13, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{p2.position.value} | OVR {ovr2}", size=10, color=ft.Colors.AMBER_300),
                ]),
            ],
        ),
        content=ft.Container(
            content=ft.Column(controls=rows, spacing=4, scroll=ft.ScrollMode.AUTO),
            width=330, height=380,
        ),
        actions=[ft.TextButton("Close", on_click=lambda e: page.pop_dialog())],
    )
    page.show_dialog(dlg)


