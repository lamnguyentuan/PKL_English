"""
Các hàm tiện ích dùng chung cho tất cả service
"""

def dictfetchall(cursor):
    """
    Hàm này giúp biến kết quả thô của SQL (dạng Tuples)
    thành dạng Dictionary (có key, value) để dễ code.
    """
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]
