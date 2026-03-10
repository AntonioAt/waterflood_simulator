"""
grid.py
-------
1-D finite-volume grid construction.
Computes cell centres, cell widths, and face permeabilities.
"""

import numpy as np
from config import RockProperties


class Grid:
    """Uniform 1-D finite-volume grid."""

    def __init__(self, rock: RockProperties):
        self.nx = rock.nx
        self.length = rock.length
        self.dx = rock.length / rock.nx
        self.x = np.linspace(self.dx / 2.0, rock.length - self.dx / 2.0, rock.nx)
        self.area = rock.area
        self.porosity = rock.porosity

        # Permeability field
        if rock.perm_array is not None:
            if len(rock.perm_array) != rock.nx:
                raise ValueError(
                    f"perm_array length {len(rock.perm_array)} != nx {rock.nx}"
                )
            self.perm = rock.perm_array.copy()
        else:
            self.perm = np.full(rock.nx, rock.permeability)

    def face_perm(self) -> np.ndarray:
        """Harmonic-average permeability at internal faces (nx-1 values)."""
        return (
            2.0 * self.perm[:-1] * self.perm[1:]
            / (self.perm[:-1] + self.perm[1:] + 1e-30)
        )

    def pore_volume_ft3(self) -> float:
        """Total pore volume in ft^3."""
        return self.porosity * self.area * self.length

    def pore_volume_bbl(self) -> float:
        """Total pore volume in barrels (1 ft^3 = 0.178107 bbl)."""
        return self.pore_volume_ft3() * 0.178107

    def __repr__(self) -> str:
        return (
            f"Grid(nx={self.nx}, L={self.length} ft, dx={self.dx:.2f} ft, "
            f"k_avg={self.perm.mean():.1f} mD)"
        )