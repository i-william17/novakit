from sqlalchemy import or_, and_
from sqlalchemy.sql import ColumnElement
from datetime import datetime


# -----------------------
# OR ILIKE (orFilterWhere ilike)
# -----------------------
def or_filter_ilike(query, model, field: str, value: str):
    if value:
        return query.where(getattr(model, field).ilike(f"%{value}%"))
    return query


# -----------------------
# AND FILTER ( andFilterWhere)
# If value is None, skip condition
# -----------------------
def and_filter(query, condition: ColumnElement, value):
    if value is not None and value != "":
        return query.where(condition)
    return query


# -----------------------
# RANGE FILTER
# Example: price >= min_price AND price <= max_price
# -----------------------
def range_filter(query, column, min_val=None, max_val=None):
    if min_val is not None:
        query = query.where(column >= min_val)
    if max_val is not None:
        query = query.where(column <= max_val)
    return query


# -----------------------
# DATE RANGE FILTER (created_at, updated_at)
# accepts strings: "2024-01-01"
# -----------------------
def date_range_filter(query, column, start_date=None, end_date=None):
    if start_date:
        dt = datetime.fromisoformat(start_date)
        query = query.where(column >= dt)

    if end_date:
        dt = datetime.fromisoformat(end_date)
        query = query.where(column <= dt)

    return query


# -----------------------
# STATUS FILTER
# -----------------------
def status_filter(query, model, status):
    if status is not None:
        return query.where(model.status == status)
    return query


# -----------------------
# MULTI FIELD SEARCH
# Example: q matches username OR email OR phone
# -----------------------
def multi_field_search(query, model, fields: list[str], term: str):
    if not term:
        return query

    conditions = [getattr(model, f).ilike(f"%{term}%") for f in fields]
    return query.where(or_(*conditions))
