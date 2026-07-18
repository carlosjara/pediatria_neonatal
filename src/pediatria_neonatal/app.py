import toga
from datetime import datetime
from toga.style import Pack
from toga.style.pack import CENTER, COLUMN, ROW

from pediatria_neonatal.application.context import create_service_context
from pediatria_neonatal.application.navigator import Navigator
from pediatria_neonatal.application.state import AppState
from pediatria_neonatal.controllers.edad_corregida_controller import (
    EdadCorregidaController,
)
from pediatria_neonatal.controllers.historial_controller import HistorialController
from pediatria_neonatal.controllers.medicion_controller import MedicionController
from pediatria_neonatal.controllers.paciente_controller import PacienteController
from pediatria_neonatal.controllers.resultado_controller import ResultadoController
from pediatria_neonatal.resources.icons import get_icons
from pediatria_neonatal.views.components import (
    SPACING_MD,
    SPACING_SM,
    SPACING_XS,
    primary_button,
    scroll_screen,
    secondary_button,
    subtitle,
    title,
    wrapped_text,
)


class PediatriaNeonatalApp(toga.App):
    def startup(self) -> None:
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.state = AppState()
        self.state.iniciar_sesion_temporal()
        self.services = create_service_context()
        self.icons = get_icons()

        self.home_content = toga.Box(style=Pack(direction=COLUMN, flex=1))
        self.patient_content = toga.Box(style=Pack(direction=COLUMN, flex=1))
        self.result_content = toga.Box(style=Pack(direction=COLUMN, flex=1))
        self.history_content = toga.Box(style=Pack(direction=COLUMN, flex=1))
        self.result_view_state = None
        self.history_snapshot_count = None

        self.navigator = Navigator(self.patient_content)
        self._init_controllers()

        self.home_shell = self._section_shell(self.home_content)
        self.patient_shell = self._section_shell(self.patient_content)
        self.result_shell = self._section_shell(self.result_content)
        self.history_shell = self._section_shell(self.history_content)

        self.tabs = toga.OptionContainer(
            content=[
                toga.OptionItem("Home", self.home_shell, icon=self.icons.home),
                toga.OptionItem("Nuevo", self.patient_shell, icon=self.icons.baby),
                toga.OptionItem(
                    "Resultados",
                    self.result_shell,
                    icon=self.icons.chart,
                ),
                toga.OptionItem(
                    "Historial",
                    self.history_shell,
                    icon=self.icons.history,
                ),
            ],
            on_select=self._on_tab_change,
        )

        self._render_home()
        self._render_empty_results()
        self._refresh_history()

        self.main_window.content = self.tabs
        self.main_window.show()
        self.tabs.current_tab = "Home"
        self._render_home()

    def _init_controllers(self) -> None:
        """Inicializa los controladores con sus callbacks."""

        self.patient_controller = PacienteController(
            state=self.state,
            on_patient_saved=self.show_measurement,
            on_calcular_edad=self.show_edad_corregida,
        )
        self.measurement_controller = MedicionController(
            state=self.state,
            services=self.services,
            on_results_ready=self.show_results,
            on_back=self.show_patient,
            on_calcular_edad=self.show_edad_corregida,
        )
        self.result_controller = ResultadoController(
            state=self.state,
            on_new_measurement=self.show_measurement,
            on_back_to_patient=self.show_patient,
        )
        self.edad_corregida_controller = EdadCorregidaController(
            state=self.state,
            on_back=self.show_patient,
        )
        self.historial_controller = HistorialController(
            state=self.state,
            on_select_result=self._show_patient_result,
        )

    def show_patient(self) -> None:
        """Muestra la pantalla de registro de paciente."""

        self.tabs.current_tab = 1 if hasattr(self, "tabs") else None
        self.navigator.show(self.patient_controller.build_view)

    def show_measurement(self) -> None:
        """Muestra la pantalla de medición antropométrica."""

        self.tabs.current_tab = 1
        self.navigator.show(self.measurement_controller.build_view)

    def show_results(self) -> None:
        """Muestra la pantalla de resultados."""

        self.tabs.current_tab = 2
        self._refresh_history()
        self._show_current_results()

    def show_edad_corregida(self) -> None:
        """Muestra la calculadora de edad corregida."""

        self.tabs.current_tab = 1
        self.navigator.show(self.edad_corregida_controller.build_view)

    def build_home(self) -> toga.Widget:
        """Construye la pantalla Home accesible desde el menú textual."""

        now = datetime.now()
        patient_count = len(self.state.pacientes_sesion)
        average_imc = self._average_session_imc()
        average_text = f"{average_imc:.2f} kg/m²" if average_imc is not None else "--"

        rows = [
            title("Home"),
            subtitle("Hola, Dra. Vanessa Jaramillo"),
            toga.Label(
                now.strftime("%H:%M"),
                style=Pack(
                    font_size=36,
                    font_weight="bold",
                    text_align=CENTER,
                    padding_top=SPACING_SM,
                    padding_bottom=SPACING_XS,
                ),
            ),
            toga.Label(
                now.strftime("%d/%m/%Y"),
                style=Pack(
                    font_size=16,
                    text_align=CENTER,
                    color="#6B7280",
                    padding_bottom=SPACING_MD,
                ),
            ),
            subtitle("Sesión actual"),
            self._session_metric_row("Pacientes registrados", str(patient_count)),
            self._session_metric_row("IMC promedio", average_text),
            toga.Label(
                "Sesión temporal activa",
                style=Pack(
                    font_size=14,
                    color="#6B7280",
                    padding_top=SPACING_SM,
                    padding_bottom=SPACING_MD,
                ),
            ),
        ]

        rows.extend(
            [
                primary_button("Nuevo paciente", lambda widget: self.show_patient()),
                secondary_button("Ver resultados", lambda w: self._show_latest()),
                secondary_button("Ver historial", lambda w: self._go_to_history()),
            ]
        )

        return scroll_screen(
            toga.Box(
                children=rows,
                style=Pack(direction=COLUMN, padding=SPACING_MD),
            )
        )

    def build_settings(self) -> toga.Widget:
        """Construye la pantalla de ajustes accesible desde el menú."""

        return scroll_screen(
            toga.Box(
                children=[
                    title("Ajustes"),
                    subtitle("Apariencia"),
                    toga.Label(
                        "Modo claro/oscuro:",
                        style=Pack(font_size=14, padding_bottom=8),
                    ),
                    toga.Label(
                        "1. Ajustes del iPhone",
                        style=Pack(font_size=14, padding_bottom=4),
                    ),
                    toga.Label(
                        "2. Pantalla y Brillo",
                        style=Pack(font_size=14, padding_bottom=4),
                    ),
                    toga.Label(
                        "3. Claro u Oscuro",
                        style=Pack(font_size=14, padding_bottom=16),
                    ),
                    toga.Button(
                        "Abrir Ajustes",
                        on_press=self._open_settings,
                        style=Pack(padding_top=8),
                    ),
                    subtitle("Información"),
                    toga.Label(
                        "Versión: 2.1 ajustes vistas e historial",
                        style=Pack(font_size=14, padding_bottom=4),
                    ),
                    toga.Label(
                        "Evaluación pediátrica neonatal",
                        style=Pack(font_size=14),
                    ),
                ],
                style=Pack(direction=COLUMN, padding=SPACING_MD),
            )
        )

    def _on_tab_change(self, widget: toga.OptionContainer) -> None:
        """Actualiza contenido cuando cambia el tab inferior."""

        if widget.current_tab.text == "Home":
            self._render_home()
        elif widget.current_tab.text == "Nuevo":
            self._render_patient_if_needed()
        elif widget.current_tab.text == "Resultados":
            if not self.state.resultados_actuales:
                self._render_empty_results()
        elif widget.current_tab.text == "Historial":
            self._refresh_history()

    def _show_current_results(self) -> None:
        """Muestra el resultado activo en la pestaña Resultados."""

        self.result_content.clear()
        self.result_content.add(self.result_controller.build_view())
        self.result_view_state = "current"

    def _show_latest(self) -> None:
        """Abre el último resultado o muestra estado vacío."""

        self.tabs.current_tab = 2
        if self.state.seleccionar_ultimo_resultado():
            self._show_current_results()
        else:
            self._render_empty_results()

    def _show_patient_result(self, index: int) -> None:
        """Abre el resultado de un paciente de la sesión."""

        self.tabs.current_tab = 2
        if self.state.seleccionar_registro_sesion(index):
            self._show_current_results()
        else:
            self._render_empty_results()

    def _render_empty_results(self) -> None:
        """Muestra estado vacío de resultados."""

        if self.result_view_state == "empty":
            return

        self.result_content.clear()
        self.result_content.add(
            scroll_screen(
                toga.Box(
                    children=[
                        title("Resultados"),
                        wrapped_text(
                            "Registro vacío. Crea un Nuevo Paciente y calcula "
                            "una medición para ver el resumen clínico.",
                            height=100,
                        ),
                        primary_button("Nuevo paciente", lambda w: self.show_patient()),
                    ],
                    style=Pack(direction=COLUMN, padding=SPACING_MD),
                )
            )
        )
        self.result_view_state = "empty"

    def _refresh_history(self) -> None:
        """Reconstruye la vista del historial."""

        current_count = len(self.state.historial_mediciones)
        if self.history_snapshot_count == current_count:
            return

        self.history_content.clear()
        self.history_content.add(self.historial_controller.build_view())
        self.history_snapshot_count = current_count

    def _go_home(self) -> None:
        self.tabs.current_tab = 0
        self._render_home()

    def _go_to_history(self) -> None:
        self.tabs.current_tab = 3
        self._refresh_history()

    def _go_to_settings(self) -> None:
        self.tabs.current_tab = 0
        self.home_content.clear()
        self.home_content.add(self.build_settings())

    def _render_home(self) -> None:
        self.home_content.clear()
        self.home_content.add(self.build_home())

    def _render_patient_if_needed(self) -> None:
        if not self.patient_content.children:
            self.navigator.show(self.patient_controller.build_view)

    def _average_session_imc(self) -> float | None:
        values = [
            float(item["imc"])
            for item in self.state.pacientes_sesion
            if item.get("imc") is not None
        ]
        if not values:
            return None
        return sum(values) / len(values)

    def _session_metric_row(self, label: str, value: str) -> toga.Box:
        return toga.Box(
            children=[
                toga.Label(
                    label,
                    style=Pack(font_size=14, color="#6B7280", flex=1),
                ),
                toga.Label(
                    value,
                    style=Pack(font_size=18, font_weight="bold", text_align=CENTER),
                ),
            ],
            style=Pack(
                direction=ROW,
                padding_top=SPACING_SM,
                padding_bottom=SPACING_SM,
            ),
        )

    def _section_shell(self, content: toga.Box) -> toga.Box:
        return toga.Box(
            children=[
                self._banner(),
                content,
            ],
            style=Pack(direction=COLUMN, flex=1),
        )

    def _banner(self) -> toga.Box:
        menu_content = toga.Box(style=Pack(direction=COLUMN))
        menu_button = toga.Button(
            "☰ Menú",
            style=Pack(width=92, font_size=12),
        )

        def toggle_menu(widget: toga.Widget) -> None:
            if menu_content.children:
                menu_content.clear()
                menu_button.text = "☰ Menú"
                return

            menu_button.text = "Cerrar"
            menu_content.add(
                self._menu_row(
                    ("Home", self._go_home),
                    ("Nuevo", self.show_patient),
                )
            )
            menu_content.add(
                self._menu_row(
                    ("Resultados", self._show_latest),
                    ("Historial", self._go_to_history),
                )
            )
            current = self.tabs.current_tab.text if hasattr(self, "tabs") else ""
            if current == "Resultados":
                menu_content.add(
                    self._menu_row(
                        ("Ver resumen", self._show_results_summary),
                        ("Ajustes", self._go_to_settings),
                    )
                )
            else:
                menu_content.add(self._menu_row(("Ajustes", self._go_to_settings)))

        menu_button.on_press = toggle_menu

        return toga.Box(
            children=[
                toga.Box(
                    children=[
                        menu_button,
                        toga.Box(style=Pack(flex=1)),
                        toga.Label(
                            "🐝",
                            style=Pack(width=48, font_size=18, text_align=CENTER),
                        ),
                    ],
                    style=Pack(direction=ROW, padding_bottom=SPACING_SM),
                ),
                menu_content,
            ],
            style=Pack(
                direction=COLUMN,
                padding_top=SPACING_SM,
                padding_bottom=SPACING_SM,
                padding_left=SPACING_MD,
                padding_right=SPACING_MD,
            ),
        )

    def _menu_row(self, *items: tuple[str, callable]) -> toga.Box:
        children = [self._menu_button(label, action) for label, action in items]
        while len(children) < 2:
            children.append(toga.Box(style=Pack(flex=1)))
        return toga.Box(
            children=children,
            style=Pack(direction=ROW, padding_bottom=SPACING_SM),
        )

    def _menu_button(self, text: str, action: callable) -> toga.Button:
        return toga.Button(
            text,
            on_press=lambda widget: action(),
            style=Pack(flex=1, padding_right=SPACING_SM),
        )

    def _show_results_summary(self) -> None:
        view = self.result_controller.view
        if view is not None:
            view.show_summary()

    def _open_settings(self, widget: toga.Widget) -> None:
        """Abre los ajustes del sistema."""

        import webbrowser

        webbrowser.open("app-settings:")


def main() -> PediatriaNeonatalApp:
    return PediatriaNeonatalApp(
        formal_name="Pediatría Neonatal",
        app_id="com.carlosjara.pediatria-neonatal",
    )
