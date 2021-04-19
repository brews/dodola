"""Objects to read and write stored climate model data.
"""

import logging
from adlfs import AzureBlobFileSystem
from fsspec.implementations.memory import MemoryFileSystem
from xarray import open_zarr


logger = logging.getLogger(__name__)


class _ZarrRepo:
    """Puts a simple read-Dataset/write-Zarr interface over fsspec-like storage

    This puts a basic read/write repository pattern over a file
    system to abstract-away the data layer. Aside from the ``read()``
    and ``write()`` methods, the additional ``get_mapper()`` method is for
    external packages that couple directly with `fsspec` to stream output
    immediately into storage.

    This is commonly instantiated through ``adl_repository``, or for testing
    with ``memory_repository``.

    Parameters
    ----------
    fs : fsspec.AbstractFileSystem-like

    See Also
    --------
    adl_repository: Instantiate a Zarr data repo using Azure Datalake Gen. 2 as backend
    memory_repository: Instantiate a Zarr data repo in memory

    """

    def __init__(self, fs):
        self._fs = fs

    def read(self, url_or_path):
        """Read Dataset from Zarr store

        Parameters
        ----------
        url_or_path : str
            Location of Zarr store to read.

        Returns
        -------
        xr.Dataset
        """
        x = open_zarr(self._fs.get_mapper(url_or_path))
        logger.info(f"Read {url_or_path}")
        return x

    def write(self, url_or_path, x):
        """Write Dataset to Zarr store

        This opens Zarr store with mode "w" and is called with with
        ``compute=True``, so any lazy computations will be completed.

        Parameters
        ----------
        url_or_path : str
            Location to write Zarr store to.
        x : xr.Dataset
        """
        x.to_zarr(self._fs.get_mapper(url_or_path), mode="w", compute=True)
        logger.info(f"Written {url_or_path}")


def adl_repository(
    account_name=None,
    account_key=None,
    client_id=None,
    client_secret=None,
    tenant_id=None,
):
    """Instantiate a Zarr data repo using Azure Datalake Gen. 2 as backend

    To authenticate with storage must pass in `account_name` and
    `account_key` for key-based authentication or `client_id`, `client_secret`,
    and `tenant_id` for authentication with service principal
    credentials. Initializing arguments are passed to ``adlfs.AzureBlobFileSystem``.

    Parameters
    ----------
    account_name : str or None, optional
    account_key : str or None, optional
    client_id : str or None, optional
    client_secret : str or None, optional
    tenant_id : str or None, optional

    Returns
    -------
    repo : dodola.repository._ZarrRepo
    """
    repo = _ZarrRepo(
        fs=AzureBlobFileSystem(
            account_name=account_name,
            account_key=account_key,
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id,
        )
    )
    return repo


def memory_repository(storage=None):
    """Instantiate a Zarr data repo in memory

    This is most commonly used for testing. Keep in mind that all instances
    share memory globally.

    Parameters
    ----------
    storage : dict or None, optional
        Mapping of `{path: data}` to immediately store into memory filesystem.

    Returns
    -------
    repo : dodola.repository._ZarrRepo
    """
    repo = _ZarrRepo(fs=MemoryFileSystem())
    for k, v in storage.items():
        repo.write(k, v)
    return repo
