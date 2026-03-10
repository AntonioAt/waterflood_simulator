"""
grid.py
=======
1-D finite-volume grid with permeability field handling.
Attaches to main via: from grid import Grid
"""

import numpy as np

from config import RockProperties


class Grid:
    """1-D finite-volume grid."""

    def __init__(self, rock: RockProperties):
        self.nx = rock.nx
        self.length = rock.length
        self.dx = rock.length / rock.nx
        self.x = np.linspace(
            self.dx / 2, rock.length - self.dx / 2, rock.nx
        )
        self.area = rock.area
        self.porosity = rock.porosity

        # Permeability field
        if rock.perm_array is not None:
            assert len(rock.perm_array) == rock.nx
            self.perm = rock.perm_array.copy()
        else:
            self.perm = np.full(rock.nx, rock.permeability)

    def face_perm(self) -> np.ndarray:
        """Harmonic average of permeability at internal faces (nx-1)."""
        return (
            2.0 * self.perm[:-1] * self.perm[1:]
            / (self.perm[:-1] + self.perm[1:] + 1e-30)
        )