import toga
from toga.style import Pack
from toga.style.pack import COLUMN

from pediatria_neonatal.application.context import (
    create_service_context,
)
from pediatria_neonatal.application.navigator import Navigator
from pediatria_neonatal.application.state import AppState
from pediatria_neonatal.controllers.historial_controller import (
    HistorialController,
)
from pediatria_neonatal.controllers.medicion_controller import (
    MedicionController,
)
from pediatria_neonatal.controllers.paciente_controller import (
    PacienteController,
)
from pediatria_neonatal.controllers.resultado_controller import (
    ResultadoController,
)
from pediatria_neonatal.resources.icons import get_icons
from pediatria_neonatal.views.components import (
    body_text,
    primary_button,
    screen_box,
    subtitle,
    title,
)


class PediatriaNeonatalApp(toga.App):
    def startup(self) -> None:
        self.state = AppState()
        self.services = create_service_context()
        self.icons = get_icons()

        self.patient_container = toga.Box(
            style=Pack(direction=COLUMN, flex=1)
        )
        self.navigator = Navigator(self.patient_container)

        self.history_container = toga.Box(
            style=Pack(direction=COLUMN, flex=1)
        )

        self._init_controllers()

        self.tabs = toga.OptionContainer(
            content=[
                toga.OptionItem(
                    "Inicio",
                    self.build_home(),
                    icon=self.icons.home,
                ),
                toga.OptionItem(
                    "Pacientes",
                    self.patient_container,
                    icon=self.icons.baby,
                ),
                toga.OptionItem(
                    "Historial",
                    self.history_container,
                    icon=self.icons.history,
                ),
                toga.OptionItem(
                    "Ajustes",
                    self.build_settings(),
                    icon=self.icons.settings,
                ),
            ],
            on_select=self._on_tab_change,
        )

        self.main_window = toga.MainWindow(
            title=self.formal_name,
        )
        self.main_window.content = self.tabs
        self.main_window.show()

        self.show_patient()

    def _init_controllers(self) -> None:
        """Inicializa los controladores con sus callbacks."""
        self.patient_controller = PacienteController(
            state=self.state,
            on_patient_saved=self.show_measurement,
        )

        self.measurement_controller = MedicionController(
            state=self.state,
            services=self.services,
            on_results_ready=self.show_results,
            on_back=self.show_patient,
        )

        self.result_controller = ResultadoController(
            state=self.state,
            on_new_measurement=self.show_measurement,
            on_back_to_patient=self.show_patient,
        )

        self.historial_controller = HistorialController(
            state=self.state,
        )

    def show_patient(self) -> None:
        """Muestra la pantalla de registro de paciente."""
        self.navigator.show(self.patient_controller.build_view)

    def show_measurement(self) -> None:
        """Muestra la pantalla de medición antropométrica."""
        self.navigator.show(self.measurement_controller.build_view)

    def show_results(self) -> None:
        """Muestra la pantalla de resultados."""
        self.navigator.show(self.result_controller.build_view)

    def build_home(self) -> toga.Widget:
        """Construye la pantalla de inicio."""
        content = screen_box(
            title("Pediatría Neonatal"),
            subtitle("Bienvenido"),
            body_text(
                "Aplicación para evaluación antropométrica "
                "de pacientes pediátricos y neonatales."
            ),
            body_text(
                "Registre un paciente en la pestaña 'Pacientes' "
                "para comenzar una evaluación."
            ),
            primary_button(
                "Nuevo paciente",
                lambda w: self._go_to_patients(),
            ),
        )
        return content

    def _go_to_patients(self) -> None:
        """Navega a la pestaña de pacientes."""
        self.tabs.current_tab = 1
        self.show_patient()

    def _on_tab_change(self, widget: toga.OptionContainer) -> None:
        """Actualiza contenido cuando cambia el tab."""
        if widget.current_tab.text == "Historial":
            self._refresh_history()

    def _refresh_history(self) -> None:
        """Reconstruye la vista del historial."""
        self.history_container.clear()
        history_view = self.historial_controller.build_view()
        self.history_container.add(history_view)

    def build_settings(self) -> toga.Widget:
        """Construye la pantalla de ajustes."""
        return screen_box(
            title("Ajustes"),
            body_text("Próximamente: configuración de la aplicación."),
        )


def main() -> PediatriaNeonatalApp:
    return PediatriaNeonatalApp(
        formal_name="Pediatría Neonatal",
        app_id="com.carlosjara.pediatria-neonatal",
    )
