#pragma once

#include <QtGlobal>

namespace AssignAndNotify {

template<typename T> bool isSame(const T &first, const T &second)
{
    return first == second;
}

inline bool isSame(qreal first, qreal second)
{
    return qFuzzyCompare(first, second);
}

}

template<typename T, typename Notify> void assignAndNotify(T &member, const T &value, Notify notify)
{
    if (AssignAndNotify::isSame(member, value))
        return;
    member = value;
    notify();
}
