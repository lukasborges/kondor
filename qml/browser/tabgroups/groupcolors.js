.pragma library

function of(name, theme) {
    const colors = {
        blue: theme.highlightColor,
        green: theme.positiveTextColor,
        orange: theme.neutralTextColor,
        red: theme.negativeTextColor,
        purple: theme.visitedLinkColor,
        gray: theme.disabledTextColor
    }
    return colors[name] ?? theme.highlightColor
}
