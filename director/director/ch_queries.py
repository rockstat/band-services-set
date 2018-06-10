
FMT_JSON = ' FORMAT JSON'
FMT_JSON_ROW = ' FORMAT JSONEachRow'


def events_where():
    return """
        date BETWEEN today() -1 AND today()
        AND timestamp > (toUInt64(now() - ((60 * 60) * 24)) * 1000)
    """


def groups(where):
    return """
        SELECT
            'sources' as group,
            session_type as param,
            uniq(uid) AS amount
        FROM events_v2
        WHERE
            name = 'session'
            AND {where}
        GROUP BY param
        ORDER BY amount desc

    UNION ALL

        SELECT
            'newusers' as group,
            if(session_num = 1, 'new users', 'returning users') as param,
            uniq(uid) AS amount
        FROM events_v2
        WHERE
            name = 'session'
            AND {where}
        GROUP BY param
        ORDER BY amount desc

    UNION ALL

        SELECT
            'devices' as group,
            mdd_device_type as param,
            uniq(uid) AS amount
        FROM events_v2
        WHERE
            name = 'session'
            AND {where}
        GROUP BY param
        ORDER BY amount desc

    """.format(where=where)


def events(where):
    return """
        SELECT
            name,
            count() AS amount
        FROM events_v2
        WHERE
            {where}
        GROUP BY name
        ORDER BY amount desc
    """
