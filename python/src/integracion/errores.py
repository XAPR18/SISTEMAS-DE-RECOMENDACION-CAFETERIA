class IntegracionError(Exception):
    """Fallo al ejecutar Scala o Prolog (proceso, tiempo de espera o respuesta ilegible)."""


class SolicitudRechazada(Exception):
    """Scala o Prolog rechazaron la solicitud por datos invalidos."""
