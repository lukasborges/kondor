#include "startupargs.h"

StartupArgs *StartupArgs::instance()
{
    static StartupArgs *args = new StartupArgs;
    return args;
}

StartupArgs *StartupArgs::create(QQmlEngine *engine, QJSEngine *jsEngine)
{
    Q_UNUSED(engine)
    Q_UNUSED(jsEngine)
    return instance();
}
