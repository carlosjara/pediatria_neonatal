"""Excepciones específicas del dominio pediátrico y neonatal."""


class ErrorDominioPediatrico(ValueError):
    """Excepción base para errores de validación del dominio.

    Hereda de ValueError porque representa datos con un tipo válido,
    pero con valores incompatibles con las reglas del sistema.
    """


class ErrorFecha(ErrorDominioPediatrico):
    """Se produce cuando una fecha es inválida o inconsistente.

    Ejemplos:
    - La fecha de medición es anterior a la fecha de nacimiento.
    - Una fecha en texto no cumple el formato ISO YYYY-MM-DD.
    """


class ErrorEdadGestacional(ErrorDominioPediatrico):
    """Se produce cuando la edad gestacional es inválida.

    Ejemplos:
    - Edad gestacional menor de 22 semanas.
    - Días gestacionales fuera del rango de 0 a 6.
    - Valores no enteros.
    """


class ErrorDatoAntropometrico(ErrorDominioPediatrico):
    """Se produce cuando peso, talla o IMC son inválidos.

    Ejemplos:
    - Peso negativo.
    - Talla igual a cero.
    - Valores no numéricos.
    - Valores incompatibles con los límites técnicos definidos.
    """


class ErrorTablaLMS(ErrorDominioPediatrico):
    """Se produce cuando una tabla LMS es inválida o incompleta.

    Ejemplos:
    - No existen parámetros para sexo y edad.
    - Los parámetros M o S son menores o iguales a cero.
    - La estructura del archivo o diccionario no es válida.
    """
