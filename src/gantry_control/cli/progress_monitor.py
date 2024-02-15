""" 

Simple methods for handling progress monitoring on loop-based actions

"""

from typing import Callable, Iterable

import tqdm

from .session import Session


class TqdmCustom(tqdm.std.tqdm):
    """
    Custom methods for handling the custom progress bar updates and interupts
    to exit out of loop level operations in certain criterias.
    """

    def __init__(self, session: Session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session  # Keeping a record of the session
        self.halt_methods = session._progress_halt_methods
        self.update_methods = session._progress_update_methods

    def update(self, n=1):
        """
        Customizing the tqdm update session. Notice that this method would not
        run everytime, but is handled by the mininterval property in vanilla
        tqdm
        """
        # Raise interupt signal for any halting method is registered under the
        # session.
        for method in self.halt_methods:
            if method(self.session):
                raise KeyboardInterrupt()

        # Running additional update methods
        for method in self.update_methods:
            method(self.session, self)
        # Always run the vanilla update method first
        return super().update(n)

    def close(self):
        for method in self.update_methods:
            method(self.session, self)
        return super().close()


def session_iterate(session: Session, x: Iterable):
    return TqdmCustom(session, x)
