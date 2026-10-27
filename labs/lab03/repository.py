from contextlib import closing

from labs.lab03.database import get_connection


def create_category(name: str) -> dict:
    """Створити нову категорію."""
    with closing(get_connection()) as connection, connection:
        cursor = connection.execute(
            "INSERT INTO categories (name) VALUES (?)",
            (name,),
        )
        category_id = cursor.lastrowid

    return {"id": category_id, "name": name}


def get_categories() -> list[dict]:
    """Отримати всі категорії за зростанням id."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()

    return [{"id": row[0], "name": row[1]} for row in rows]


def delete_category(category_id: int) -> bool:
    """Видалити категорію за її id."""
    with closing(get_connection()) as connection, connection:
        cursor = connection.execute(
            "DELETE FROM categories WHERE id = ?",
            (category_id,),
        )
        return cursor.rowcount > 0


def get_record(record_id: int) -> dict | None:
    """Отримати запис за id разом із назвою категорії."""
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT r.id, r.code, r.title, r.category_id,
                   r.value, r.status, c.name
            FROM records AS r
            JOIN categories AS c ON r.category_id = c.id
            WHERE r.id = ?
            """,
            (record_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "code": row[1],
        "title": row[2],
        "category_id": row[3],
        "value": row[4],
        "status": row[5],
        "category_name": row[6],
    }


def create_record(
    code: str,
    title: str,
    category_id: int,
    value: float,
    status: str,
) -> dict:
    """Створити запис у базі даних."""
    with closing(get_connection()) as connection, connection:
        cursor = connection.execute(
            """
            INSERT INTO records
                (code, title, category_id, value, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (code, title, category_id, value, status),
        )
        record_id = cursor.lastrowid

    return get_record(record_id)


def update_record(
    record_id: int,
    code: str,
    title: str,
    category_id: int,
    value: float,
    status: str,
) -> dict | None:
    """Повністю оновити змінювані поля запису."""
    with closing(get_connection()) as connection, connection:
        cursor = connection.execute(
            """
            UPDATE records
            SET code = ?, title = ?, category_id = ?,
                value = ?, status = ?
            WHERE id = ?
            """,
            (
                code,
                title,
                category_id,
                value,
                status,
                record_id,
            ),
        )

        if cursor.rowcount == 0:
            return None

    return get_record(record_id)


def delete_record(record_id: int) -> bool:
    """Видалити запис за його id."""
    with closing(get_connection()) as connection, connection:
        cursor = connection.execute(
            "DELETE FROM records WHERE id = ?",
            (record_id,),
        )
        return cursor.rowcount > 0


def get_records(
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """Отримати записи з фільтрацією та пагінацією."""
    query = """
        SELECT r.id, r.code, r.title, r.category_id,
               r.value, r.status, c.name
        FROM records AS r
        JOIN categories AS c ON r.category_id = c.id
        WHERE 1 = 1
    """

    params = []

    if category_id is not None:
        query += " AND r.category_id = ?"
        params.append(category_id)

    if status is not None:
        query += " AND r.status = ?"
        params.append(status)

    if min_value is not None:
        query += " AND r.value >= ?"
        params.append(min_value)

    if q is not None:
        query += " AND instr(r.title, ?) > 0"
        params.append(q)

    query += " ORDER BY r.id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with closing(get_connection()) as connection:
        rows = connection.execute(query, params).fetchall()

    return [
        {
            "id": row[0],
            "code": row[1],
            "title": row[2],
            "category_id": row[3],
            "value": row[4],
            "status": row[5],
            "category_name": row[6],
        }
        for row in rows
    ]


def create_records_bulk(records: list[dict]) -> list[dict]:
    """Створити пакет записів в одній транзакції."""
    created_ids = []

    with closing(get_connection()) as connection, connection:
        for record in records:
            cursor = connection.execute(
                """
                INSERT INTO records
                    (code, title, category_id, value, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record["code"],
                    record["title"],
                    record["category_id"],
                    record["value"],
                    record["status"],
                ),
            )
            created_ids.append(cursor.lastrowid)

    return [get_record(record_id) for record_id in created_ids]
