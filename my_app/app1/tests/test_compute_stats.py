# # myapp/tests/test_compute_stats.py

# import numpy as np
# from django.test import TestCase

from app1.api.views import _compute_stats

# # Importa la función _compute_stats desde donde la tengas:
# # por ejemplo: from myapp.views import _compute_stats
# from myapp.views import _compute_stats

# class ComputeStatsUnitTest(TestCase):
#     def test_compute_stats_valores_distintos(self):
#         """
#         Lista [1, 2, 3, 4] con percentiles [25, 50, 75].
#         - Media = 2.5
#         - Desviación poblacional = sqrt(((−1.5)^2 + (−0.5)^2 + (0.5)^2 + (1.5)^2)/4) ≈ 1.1180
#         - p25 = 1.75, p50 = 2.5, p75 = 3.25
#         """
#         valores = [1, 2, 3, 4]
#         percentiles = [25, 50, 75]
#         resultado = _compute_stats(valores, percentiles)

#         # Media
#         self.assertAlmostEqual(resultado['mean'], 2.5, places=6)

#         # Desviación poblacional: usa numpy para comparar
#         arr = np.array(valores, dtype=float)
#         self.assertAlmostEqual(resultado['sd'], float(arr.std(ddof=0)), places=6)

#         # Percentiles
#         esperados_pct = {'25': 1.75, '50': 2.5, '75': 3.25}
#         self.assertEqual(resultado['percentiles'], esperados_pct)

#     def test_compute_stats_valores_iguales(self):
#         """
#         Si todos los valores son iguales, 
#         la media = ese valor, desviación = 0, todos los percentiles = ese valor.
#         """
#         valores = [5, 5, 5, 5]
#         percentiles = [0, 50, 100]
#         resultado = _compute_stats(valores, percentiles)

#         # Media
#         self.assertEqual(resultado['mean'], 5.0)
#         # Desviación
#         self.assertEqual(resultado['sd'], 0.0)
#         # Todos los percentiles deben ser 5.0
#         self.assertEqual(resultado['percentiles'], {'0': 5.0, '50': 5.0, '100': 5.0})

#     def test_compute_stats_lista_un_elemento(self):
#         """
#         Con una sola entrada [x], la media = x, desviación = 0, 
#         cualquier percentil = x.
#         """
#         valores = [42.0]
#         percentiles = [10, 50, 90]
#         resultado = _compute_stats(valores, percentiles)

#         self.assertEqual(resultado['mean'], 42.0)
#         self.assertEqual(resultado['sd'], 0.0)
#         for clave, valor in resultado['percentiles'].items():
#             self.assertEqual(valor, 42.0)

#     def test_compute_stats_lista_vacia(self):
#         """
#         Definir el comportamiento cuando la lista está vacía. 
#         Según implementación actual con numpy, np.percentile([],…) lanza ValueError.
#         Podemos esperar que la función al pasar [] levante excepcion o devuelva algo específico.
#         Aquí comprobaremos que lanza ValueError.
#         """
#         with self.assertRaises(ValueError):
#             _compute_stats([], [50])

# myapp/tests/test_compute_stats_pytest.py

import numpy as np
import pytest

# from myapp.views import _compute_stats

def test_compute_stats_valores_distintos_pytest():
    valores = [1, 2, 3, 4]
    percentiles = [25, 50, 75]
    resultado = _compute_stats(valores, percentiles)

    # Media
    assert resultado['mean'] == pytest.approx(2.5, rel=1e-6)

    # Desviación poblacional
    arr = np.array(valores, dtype=float)
    assert resultado['sd'] == pytest.approx(float(arr.std(ddof=0)), rel=1e-6)

    # Percentiles
    esperados_pct = {'25': 1.75, '50': 2.5, '75': 3.25}
    assert resultado['percentiles'] == esperados_pct

def test_compute_stats_valores_iguales_pytest():
    valores = [5, 5, 5, 5]
    percentiles = [0, 50, 100]
    resultado = _compute_stats(valores, percentiles)

    assert resultado['mean'] == 5.0
    assert resultado['sd'] == 0.0
    assert resultado['percentiles'] == {'0': 5.0, '50': 5.0, '100': 5.0}

def test_compute_stats_lista_un_elemento_pytest():
    valores = [42.0]
    percentiles = [10, 50, 90]
    resultado = _compute_stats(valores, percentiles)

    assert resultado['mean'] == 42.0
    assert resultado['sd'] == 0.0
    for valor in resultado['percentiles'].values():
        assert valor == 42.0

def test_compute_stats_lista_vacia_pytest():
    # with pytest.raises(ValueError):
    resultado= _compute_stats([], [50])
    assert resultado['mean'] == 0.0
    assert resultado['sd'] == 0.0
    assert resultado['percentiles'] == {'50': 0.0}