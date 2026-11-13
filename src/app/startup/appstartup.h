#pragma once

#include "app/commandline/commandline.h"
#include "app/instance/singleinstance.h"

class QApplication;
class QQmlApplicationEngine;

bool forwardsToRunningInstance(SingleInstance &singleInstance, const CommandLine &commandLine);
void startBrowser(QApplication &app, const CommandLine &commandLine);
bool openWindows(QQmlApplicationEngine &engine, SingleInstance &singleInstance);
