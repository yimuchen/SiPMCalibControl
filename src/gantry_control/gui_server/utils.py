"""

Additionaly utility objects to assist with GUI session running.

"""
import tqdm

from .session import GUISession  # For typing

# from .sync_socket import sync_action_progress


class TqdmCustom(tqdm.std.tqdm):
    def __init__(self, session: GUISession, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    def update(self, n=1):
        """
        Customizing the update function for additional checks. Notice that the
        update function will only be ran every mininterval, so not nessecarily
        on every interation. Also note that here we will purely be updating the
        various update functions and raising excpetions. The handling of these
        function will be implemented elsewhere.
        """
        super().update(n=n)  # Always run the trivial upstream function first
        sync_action_progress(self.session)
        print("My custom access")


# Due to cyclic dependencies
