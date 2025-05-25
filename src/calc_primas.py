"""
Descripción
===========
Este modulo implementa funciones utilizadas para la cotizacón de primas de seguros.

Funciones
===========
"""

def calcular_edad(fecha_nac, fecha_ref):
    """
    Calcula la edad de una persona a partir de su fecha de nacimiento y una fecha de referencia.

    Parameters:
        fecha_nac (datetime.date): Fecha de nacimiento de la persona.
        fecha_ref (datetime.date): Fecha de referencia para el cálculo de la edad.

    Returns:
        int: Edad de la persona en años.
    """
    # Verifica si la fecha de referencia es anterior a la fecha de nacimiento
    if fecha_ref < fecha_nac:
        # Si es así, devuelve un valor negativo para indicar un error
        return -1
    return fecha_ref.year - fecha_nac.year - ((fecha_ref.month, fecha_ref.day) < (fecha_nac.month, fecha_nac.day))