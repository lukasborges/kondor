PACKAGE_SUFFIX = ".kondorext"


def has_package_suffix(path: str) -> bool:
    return path.lower().endswith(PACKAGE_SUFFIX)
