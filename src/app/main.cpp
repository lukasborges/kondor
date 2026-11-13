#include "app/startup/appidentity.h"
#include "app/startup/appstartup.h"
#include "app/commandline/commandline.h"
#include "app/startup/environment.h"
#include "app/startup/messagehandler.h"

#include <QApplication>
#include <QQmlApplicationEngine>

int main(int argc, char *argv[])
{
    installMessageHandler();
    prepareEnvironment();
    QApplication app(argc, argv);
    setUpIdentity();
    const CommandLine commandLine = parseCommandLine(app);
    SingleInstance singleInstance;
    if (forwardsToRunningInstance(singleInstance, commandLine)) return 0;
    startBrowser(app, commandLine);
    QQmlApplicationEngine engine;
    return openWindows(engine, singleInstance) ? app.exec() : 1;
}
