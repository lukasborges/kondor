#pragma once

#include <QObject>

class ExtensionBridge;

class ExtensionPageApi : public QObject
{
    Q_OBJECT

public:
    explicit ExtensionPageApi(ExtensionBridge *bridge);

    Q_INVOKABLE QString request(const QString &requestJson);

private:
    ExtensionBridge *m_bridge;
};
