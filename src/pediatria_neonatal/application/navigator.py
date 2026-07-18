from collections.abc import Callable

import toga


ViewFactory = Callable[[], toga.Widget]


class Navigator:
    """Controla la pantalla mostrada en la pestaña de pacientes."""

    def __init__(self, container: toga.Box) -> None:
        self.container = container

    def show(self, factory: ViewFactory) -> None:
        view = factory()

        self.container.clear()
        self.container.add(view)
