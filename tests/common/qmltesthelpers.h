#pragma once

#include <QJSEngine>
#include <QMetaObject>
#include <QObject>
#include <QQmlEngine>
#include <QString>

inline QObject *findByClassName(QObject *parent, const QString &className)
{
    for (QObject *child : parent->children()) {
        if (QString::fromLatin1(child->metaObject()->className()).contains(className))
            return child;
        if (QObject *found = findByClassName(child, className))
            return found;
    }
    return nullptr;
}

template<typename T>
void registerSingleton(const char *name)
{
    qmlRegisterSingletonType<T>("Kondor", 1, 0, name, [](QQmlEngine *, QJSEngine *) -> QObject * {
        QQmlEngine::setObjectOwnership(T::instance(), QQmlEngine::CppOwnership);
        return T::instance();
    });
}
