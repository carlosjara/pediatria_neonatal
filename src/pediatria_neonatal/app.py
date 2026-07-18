import toga
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
    body_text,
    caption_text,
    field_label,
    primary_button,
    scroll_screen,
    secondary_button,
    subtitle,
    title,
)


class PediatriaNeonatalApp(toga.App):
    def startup(self) -> None:
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.state = AppState()
        self.state.iniciar_sesion_temporal()
        self.services = create_service_context()
        self.icons = get_icons()

        self.workspace_content = toga.Box(style=Pack(direction=COLUMN, flex=1))
        self.result_content = toga.Box(style=Pack(direction=COLUMN, flex=1))
        self.history_content = toga.Box(style=Pack(direction=COLUMN, flex=1))

        self.navigator = Navigator(self.workspace_content)
        self._init_controllers()

        self.workspace_shell = self._section_shell(self.workspace_content)
        self.result_shell = self._section_shell(self.result_content)
        self.history_shell = self._section_shell(self.history_content)

        self.tabs = toga.OptionContainer(
            content=[
                toga.OptionItem("Nuevo", self.workspace_shell, icon=self.icons.baby),
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

        self.show_patient()
        self._render_empty_results()
        self._refresh_history()

        self.main_window.content = self.tabs
        self.main_window.show()

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
        self.historial_controller = HistorialController(state=self.state)

    def show_patient(self) -> None:
        """Muestra la pantalla de registro de paciente."""

        self.tabs.current_tab = 0 if hasattr(self, "tabs") else None
        self.navigator.show(self.patient_controller.build_view)

    def show_measurement(self) -> None:
        """Muestra la pantalla de medición antropométrica."""

        self.tabs.current_tab = 0
        self.navigator.show(self.measurement_controller.build_view)

    def show_results(self) -> None:
        """Muestra la pantalla de resultados."""

        self.tabs.current_tab = 1
        self._refresh_history()
        self._show_current_results()

    def show_edad_corregida(self) -> None:
        """Muestra la calculadora de edad corregida."""

        self.tabs.current_tab = 0
        self.navigator.show(self.edad_corregida_controller.build_view)

    def build_home(self) -> toga.Widget:
        """Construye la pantalla Home accesible desde el menú textual."""

        rows = [
            title("Home"),
            subtitle("Hola, Dra. Vanessa Jaramillo"),
            caption_text(
                "Sesión temporal activa. En la próxima versión se agregará "
                "manejo de sesiones con base de datos local persistida."
            ),
            subtitle("Pacientes registrados"),
        ]

        if not self.state.pacientes_sesion:
            rows.append(
                body_text(
                    "Aún no hay pacientes evaluados. Registra un Nuevo Paciente "
                    "para habilitar Resultados e Historial.",
                    height=90,
                )
            )
        else:
            for index, paciente in enumerate(self.state.pacientes_sesion):
                rows.append(self._patient_session_row(index, paciente))

        rows.extend(
            [
                primary_button("Nuevo paciente", lambda w: self.show_patient()),
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

        if widget.current_tab.text == "Resultados":
            if not self.state.resultados_actuales:
                self._render_empty_results()
        elif widget.current_tab.text == "Historial":
            self._refresh_history()

    def _show_current_results(self) -> None:
        """Muestra el resultado activo en la pestaña Resultados."""

        self.result_content.clear()
        self.result_content.add(self.result_controller.build_view())

    def _show_latest(self) -> None:
        """Abre el último resultado o muestra estado vacío."""

        self.tabs.current_tab = 1
        if self.state.seleccionar_ultimo_resultado():
            self._show_current_results()
        else:
            self._render_empty_results()

    def _show_patient_result(self, index: int) -> None:
        """Abre el resultado de un paciente de la sesión."""

        self.tabs.current_tab = 1
        if self.state.seleccionar_registro_sesion(index):
            self._show_current_results()
        else:
            self._render_empty_results()

    def _render_empty_results(self) -> None:
        """Muestra estado vacío de resultados."""

        self.result_content.clear()
        self.result_content.add(
            scroll_screen(
                toga.Box(
                    children=[
                        title("Resultados"),
                        body_text(
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

    def _refresh_history(self) -> None:
        """Reconstruye la vista del historial."""

        self.history_content.clear()
        self.history_content.add(self.historial_controller.build_view())

    def _go_home(self) -> None:
        self.tabs.current_tab = 0
        self.workspace_content.clear()
        self.workspace_content.add(self.build_home())

    def _go_to_history(self) -> None:
        self.tabs.current_tab = 2
        self._refresh_history()

    def _go_to_settings(self) -> None:
        self.tabs.current_tab = 0
        self.workspace_content.clear()
        self.workspace_content.add(self.build_settings())

    def _patient_session_row(self, index: int, paciente: dict) -> toga.Box:
        edad = paciente.get("edad", "")
        corregida = paciente.get("edad_corregida", "")
        edad_texto = f"Edad: {edad}"
        if corregida:
            edad_texto = f"{edad_texto} · Corregida: {corregida}"

        return toga.Box(
            children=[
                field_label(str(paciente.get("nombre") or "Paciente")),
                caption_text(edad_texto),
                toga.Button(
                    "Ver resultado",
                    on_press=lambda w, item_index=index: self._show_patient_result(
                        item_index
                    ),
                    style=Pack(padding_top=SPACING_SM, padding_bottom=SPACING_SM),
                ),
            ],
            style=Pack(
                direction=COLUMN,
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
        return toga.Box(
            children=[
                toga.Box(
                    children=[
                        toga.Label(
                            "Menú",
                            style=Pack(width=70, font_size=12, font_weight="bold"),
                        ),
                        toga.Label(
                            "Pediatría Neonatal",
                            style=Pack(
                                flex=1,
                                font_size=16,
                                font_weight="bold",
                                text_align=CENTER,
                            ),
                        ),
                        toga.Label(
                            "🐝",
                            style=Pack(width=48, font_size=18, text_align=CENTER),
                        ),
                    ],
                    style=Pack(direction=ROW, padding_bottom=SPACING_SM),
                ),
                toga.Box(
                    children=[
                        toga.Button("Home", on_press=lambda w: self._go_home()),
                        toga.Button("Nuevo", on_press=lambda w: self.show_patient()),
                        toga.Button(
                            "Resultados",
                            on_press=lambda w: self._show_latest(),
                        ),
                    ],
                    style=Pack(direction=ROW, padding_bottom=SPACING_SM),
                ),
                toga.Box(
                    children=[
                        toga.Button(
                            "Historial",
                            on_press=lambda w: self._go_to_history(),
                        ),
                        toga.Button(
                            "Ajustes",
                            on_press=lambda w: self._go_to_settings(),
                        ),
                    ],
                    style=Pack(direction=ROW),
                ),
            ],
            style=Pack(
                direction=COLUMN,
                padding_top=SPACING_SM,
                padding_bottom=SPACING_SM,
                padding_left=SPACING_MD,
                padding_right=SPACING_MD,
            ),
        )

    def _open_settings(self, widget: toga.Widget) -> None:
        """Abre los ajustes del sistema."""

        import webbrowser

        webbrowser.open("app-settings:")


def main() -> PediatriaNeonatalApp:
    return PediatriaNeonatalApp(
        formal_name="Pediatría Neonatal",
        app_id="com.carlosjara.pediatria-neonatal",
    )
