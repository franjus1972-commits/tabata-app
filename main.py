import asyncio
import flet as ft

async def main(page: ft.Page):
    page.title = "Cronómetro Tabata"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0b0e14"
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    beep_sound = ft.Audio(
        src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg", 
        autoplay=False
    )
    finish_sound = ft.Audio(
        src="https://actions.google.com/sounds/v1/ambiences/cheering.ogg", 
        autoplay=False
    )
    page.overlay.extend([beep_sound, finish_sound])

    is_running = False
    is_paused = False
    current_task = None

    input_work = ft.TextField(
        label="Ejercicio (segundos)",
        value="20",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=280,
    )
    input_break = ft.TextField(
        label="Descanso (segundos)",
        value="10",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=280,
    )
    input_rounds = ft.TextField(
        label="Rondas",
        value="8",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=280,
    )

    phase_badge = ft.Container(
        content=ft.Text("LISTO", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
        bgcolor=ft.Colors.BLUE_GREY_700,
        padding=ft.padding.symmetric(horizontal=16, vertical=6),
        border_radius=15,
    )
    
    progress_ring = ft.ProgressRing(
        value=1.0, 
        stroke_width=10, 
        width=220, 
        height=220, 
        color=ft.Colors.GREEN_400
    )
    
    countdown_text = ft.Text("0", size=54, weight=ft.FontWeight.BOLD)
    timer_label = ft.Text("Listo", size=16, color=ft.Colors.WHITE70)
    
    ring_stack = ft.Stack(
        controls=[
            progress_ring,
            ft.Container(
                content=ft.Column(
                    [countdown_text, timer_label],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                width=220,
                height=220,
            )
        ],
        alignment=ft.alignment.center
    )

    round_title = ft.Text("Ronda 1 / 8", size=22, weight=ft.FontWeight.W_600)
    round_dots_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, wrap=True)

    home_screen = ft.Column(
        controls=[
            ft.Text("Cronómetro Tabata", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
            ft.Text(
                "Temporizador de intervalos para entrenar.",
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.WHITE70,
            ),
            ft.Container(height=15),
            input_work,
            input_break,
            input_rounds,
            ft.Container(height=15),
            ft.ElevatedButton(
                "Empezar",
                on_click=lambda _: start_workout_flow(),
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                    padding=15
                ),
                width=280
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    btn_pause = ft.ElevatedButton("Pausar", on_click=lambda _: toggle_pause())
    
    work_screen = ft.Column(
        controls=[
            phase_badge,
            ft.Container(height=15),
            ring_stack,
            ft.Container(height=15),
            round_title,
            round_dots_row,
            ft.Container(height=20),
            ft.Row(
                [
                    btn_pause,
                    ft.OutlinedButton(
                        "Finalizar", 
                        on_click=lambda _: show_confirm_finish_dialog(),
                        style=ft.ButtonStyle(color=ft.Colors.RED_400)
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=15
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        visible=False
    )

    page.add(ft.Column([home_screen, work_screen], alignment=ft.MainAxisAlignment.CENTER))

    def update_dots(total_rounds, current_round):
        round_dots_row.controls.clear()
        for i in range(1, total_rounds + 1):
            color = ft.Colors.BLUE_400 if i <= current_round else ft.Colors.GREY_700
            round_dots_row.controls.append(
                ft.Container(width=12, height=12, border_radius=6, bgcolor=color)
            )

    def toggle_pause():
        nonlocal is_paused
        is_paused = not is_paused
        btn_pause.text = "Reanudar" if is_paused else "Pausar"
        page.update()

    def reset_to_home():
        nonlocal is_running, is_paused
        is_running = False
        is_paused = False
        btn_pause.text = "Pausar"
        work_screen.visible = False
        home_screen.visible = True
        page.update()

    def show_confirm_finish_dialog():
        nonlocal is_paused
        is_paused = True
        btn_pause.text = "Reanudar"
        page.update()

        def confirm(yes):
            page.close(dialog)
            if yes:
                if current_task:
                    current_task.cancel()
                reset_to_home()

        dialog = ft.AlertDialog(
            title=ft.Text("¿Finalizar entrenamiento?"),
            actions=[
                ft.TextButton("Seguir", on_click=lambda e: confirm(False)),
                ft.TextButton("Finalizar", on_click=lambda e: confirm(True)),
            ]
        )
        page.open(dialog)

    def start_workout_flow():
        try:
            work_sec = int(input_work.value)
            break_sec = int(input_break.value)
            rounds_cnt = int(input_rounds.value)
            if work_sec < 1 or break_sec < 1 or rounds_cnt < 1:
                return
        except ValueError:
            return

        nonlocal current_task
        home_screen.visible = False
        work_screen.visible = True
        current_task = asyncio.create_task(run_workout_logic(work_sec, break_sec, rounds_cnt))

    async def run_workout_logic(work_sec, break_sec, total_rounds):
        nonlocal is_running, is_paused
        is_running = True
        is_paused = False

        for r in range(1, total_rounds + 1):
            round_title.value = f"Ronda {r} / {total_rounds}"
            update_dots(total_rounds, r)

            phase_badge.bgcolor = ft.Colors.GREEN_600
            phase_badge.content.value = "EJERCICIO"
            progress_ring.color = ft.Colors.GREEN_400
            timer_label.value = "¡A entrenar!"
            await run_phase(work_sec)

            if not is_running:
                return

            if r < total_rounds:
                phase_badge.bgcolor = ft.Colors.ORANGE_700
                phase_badge.content.value = "DESCANSO"
                progress_ring.color = ft.Colors.ORANGE_400
                timer_label.value = "Descansa"
                await run_phase(break_sec)

                if not is_running:
                    return

        finish_sound.play()
        reset_to_home()

    async def run_phase(seconds):
        total = seconds
        current = seconds
        while current > 0:
            if not is_running:
                break
            while is_paused:
                await asyncio.sleep(0.1)

            if current <= 3:
                beep_sound.play()

            countdown_text.value = str(current)
            progress_ring.value = current / total
            page.update()

            await asyncio.sleep(1)
            current -= 1

ft.app(target=main)
