from PySide6.QtCore import QUrl

from kondor.extensions.package.packagesuffix import has_package_suffix


def is_local_package(url: QUrl) -> bool:
    return url.isLocalFile() and has_package_suffix(url.toLocalFile())


def take_extension_packages(urls: list[QUrl]) -> list[str]:
    packages = [url for url in urls if is_local_package(url)]
    urls[:] = [url for url in urls if not is_local_package(url)]
    return [url.toLocalFile() for url in packages]
