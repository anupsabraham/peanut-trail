from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import Query


@dataclass
class TransactionFilters:
    page: Annotated[int, Query(ge=1)] = 1
    category: Annotated[str, Query()] = ""
    vendor: Annotated[str, Query()] = ""
    start_date: Annotated[date | None, Query()] = None
    end_date: Annotated[date | None, Query()] = None
    search: Annotated[str, Query()] = ""
    min_amount: Annotated[Decimal | None, Query()] = None
    max_amount: Annotated[Decimal | None, Query()] = None
    exclude_filter: Annotated[str, Query()] = ""
