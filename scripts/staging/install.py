import compileall
import shutil
from pathlib import Path

PACKAGING_FILES = (
    ("kondor.desktop", "share/applications"),
    ("io.github.lukasborges.Kondor.metainfo.xml", "share/metainfo"),
    ("kondor-extension.xml", "share/mime/packages"),
    ("io.github.lukasborges.Kondor.krunner.desktop", "share/krunner/dbusplugins"),
    ("kondor.png", "share/icons/hicolor/256x256/apps"),
    ("kondor.svg", "share/icons/hicolor/scalable/apps"),
)
ACTION_ICONS = ("kondor-extensions-symbolic.svg",)
NOT_INSTALLED = ("kondor.qrc", "i18n")


def install_staged_files(staged: Path, share: Path) -> None:
    shutil.copytree(
        staged, share, ignore=shutil.ignore_patterns(*NOT_INSTALLED), dirs_exist_ok=True
    )


def install_python_package(repository: Path, share: Path) -> None:
    for source in sorted((repository / "src" / "kondor").rglob("*.py")):
        target = share / source.relative_to(repository / "src")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    compileall.compile_dir(share / "kondor", quiet=1)


def install_launcher(repository: Path, prefix: Path) -> None:
    target = prefix / "bin" / "kondor"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(repository / "packaging" / "kondor", target)
    target.chmod(0o755)


def install_packaging_files(repository: Path, prefix: Path) -> None:
    for name, folder in PACKAGING_FILES:
        target = prefix / folder
        target.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repository / "packaging" / name, target / name)


def install_action_icons(repository: Path, prefix: Path) -> None:
    source = repository / "assets" / "icons" / "hicolor" / "scalable" / "actions"
    target = prefix / "share" / "icons" / "hicolor" / "scalable" / "actions"
    target.mkdir(parents=True, exist_ok=True)
    for name in ACTION_ICONS:
        shutil.copyfile(source / name, target / name)


def install(repository: Path, staged: Path, prefix: Path) -> None:
    share = prefix / "share" / "kondor"
    install_staged_files(staged, share)
    install_python_package(repository, share)
    install_launcher(repository, prefix)
    install_packaging_files(repository, prefix)
    install_action_icons(repository, prefix)
